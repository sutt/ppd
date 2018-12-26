import sys, copy, random, subprocess, time
import pickle
import cv2
import numpy as np
import io
import pandas as pd
from PIL import Image
from collections import OrderedDict
from itertools import combinations
from Interproc import DBInterface
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from Interproc import GuiviewState
from ControlTracking import TrackFactory
from ControlDisplay import Display



class EvalTracker:

    '''
        Different ways to evaluate if the ScoreSchema output from a trackFrame
        matches expectations.

        inputs are full scoring-dict, within this class we index the scoring-dict
        with 'objEnum' and 'data' keys

            e.g. EvalTracker.setBaselineScore(gs.displayInputScore)
                 (where gs.displayInputScore is a score-dict)

    '''
    
    def __init__(self):
        self.baselineScore = None
        self.objEnum = '0'

    def setObjEnum(self, sObjEnum):
        self.objEnum = str(sObjEnum)

    def setBaselineScore(self, baselineScore):
        self.baselineScore = copy.deepcopy(baselineScore)

    def distanceFromBaseline(self, inputScore):
        ''' cartesian distance from center of inputScore to baseline;
            for score-type=circle only
        '''
        
        if not(self.checkTrackSuccess(inputScore)):
            return 9999.9

        xA, yA, rA = Display.rectToCircle(inputScore[self.objEnum]['data'])
        xB, yB, rB = Display.rectToCircle(self.baselineScore[self.objEnum]['data'])

        cartDistance = ((xA - xB)**2 + (yA - yB)**2)**(0.5)

        return cartDistance

    def checkTrackSuccess(self, trackScore):
        ''' easiest way to check a ScoreSchema if track returned True '''
        try:
            if trackScore[self.objEnum]['data'] == (0,0,0,0):
                return False
            return True
        except:
            return False

    def checkTrackInsideBaselineRect(self, inputScore):
        '''
            check if the center on inputScore is inside the baslineScore
            important: this uses rect, not circle    
        '''
        
        if not(self.checkTrackSuccess(inputScore)):
            return False

        _x, _y, _dx, _dy = inputScore['0']['data']
        x, y, dx, dy = self.baselineScore['0']['data']

        if not((_x > x) and (_x < x + dx)):
            return False

        if not((_y > y) and (_y < y + dy)):        
            return False
        
        return True

    def checkTrackInsideBaseline(self, inputScore):
        '''
            check if the center on inputScore is inside the baslineScore
            considered as a circle
                
        '''
        
        if not(self.checkTrackSuccess(inputScore)):
            return False

        xB, yB, rB = Display.rectToCircle(self.baselineScore[self.objEnum]['data'])

        dist = self.distanceFromBaseline(inputScore)

        if dist < rB:
            return True

        return False


    def checkBaselineInsideTrack(self, inputScore):
        '''
            check if the center on baselineScore is inside the trackScore
                currently inside rect; todo - check for inside a circle
        '''
        
        if not(self.checkTrackSuccess(inputScore)):
            return False

        xA, yA, rA = Display.rectToCircle(inputScore[self.objEnum]['data'])

        dist = self.distanceFromBaseline(inputScore)

        if dist < rA:
            return True

        return False

    def checkEitherContainsOther(self, inputScore):
        ''' either track-center is inside baseline-score-circle or
            baseline-score-center is inside track-center-circle. '''

        return ( self.checkBaselineInsideTrack(inputScore) or
                self.checkTrackInsideBaseline(inputScore))

    def checkBothContainsOther(self, inputScore):
        ''' both track-center is inside baseline-score-circle and
            baseline-score-center is inside track-center-circle. '''

        return ( self.checkBaselineInsideTrack(inputScore) and
                self.checkTrackInsideBaseline(inputScore))


    def compareRadii(self, inputScore):
        '''
            compare size of the radius;
            positive: track is larger; nnegative: baseline is larger
        '''
        
        xA, yA, rA = Display.rectToCircle(inputScore[self.objEnum]['data'])
        xB, yB, rB = Display.rectToCircle(self.baselineScore[self.objEnum]['data'])

        if ((rA > 0.0) and (rB > 0.0)):
            return (rA - rB)
        else:
            return 0.0


    def checkTrackInWindow(self, inputScore, zoomRect):
        '''
            check if inputScore is inside the zoomWindow
            question: is zoomrect relative to Orig or to Main?
        '''
        pass


class EvalDataset:

    ''' put eval results into a dataframe '''

    def __init__(self):
        
        self.df = None
        self.eval_method_names = [
            'checkBaselineInsideTrack',
            'checkBothContainsOther',
            'checkEitherContainsOther',
            'checkTrackInWindow',
            'checkTrackInsideBaseline',
            'checkTrackInsideBaselineRect',
            'checkTrackSuccess',
            'compareRadii',
            'distanceFromBaseline'
            ]


    def buildDataset(self, listGS, tracker):
        ''' return: pd.DataFrame
            input:  listGS - list of GuiveiwState objects
                    tracker - TrackFactory object, initialized
            
            Helper Function to build a table of eval performance data
            for multiple frames.

                rows corresponding to frames/gs's
                cols corresponding to EvalTracker properties
        '''

        eval_data = self.buildEvalData(listGS, tracker, self.eval_method_names)
        index_data = self.buildIndexData(listGS)
        full_data = self.mergeDataDicts(*[index_data, eval_data])
        
        df = pd.DataFrame(full_data)

        self.df = df
        
        return df


    @staticmethod
    def evalRecord(gs, tracker, method_names):
        ''' return a list of values (double, int, str, bool, obj) corresponding
            to the result an EvalTracker method for that gs. Order of list
            corresponds to order of method_names'''
        
        list_data = []

        try:
            _ev = EvalTracker()
            _ev.setBaselineScore(gs.displayInputScore)

            tracker.setFrame(gs.getOrigFrame())
            tracker.trackFrame()
            
            _trackScore = tracker.getTrackScore()
            
        except:        
            return None
        
        for meth_name in method_names:

            try:
                _evMeth = getattr(_ev, meth_name)
                _val = _evMeth(_trackScore)
            except:
                _val = None
            
            list_data.append(_val)

        return list_data


    @classmethod
    def buildEvalData(cls, listGS, tracker, eval_method_names):
        
        data = []
        
        for _gs in listGS:
            
            _record = cls.evalRecord(_gs, tracker, copy.copy(eval_method_names))
            
            data.append(_record)
            
        dict_data = {}
        
        for j_col in range(len(eval_method_names)):
            
            _tmp = []
            
            for i_row in range(len(data)):
            
                _tmp.append(data[i_row][j_col])
            
            dict_data[eval_method_names[j_col]] = _tmp
            
        return dict_data

    @staticmethod
    def buildIndexData(listGS):
        
        data_ind = []
        data_frameCounter = []
        
        for _ind, _gs in enumerate(listGS):
            
            data_ind.append(_ind)
            data_frameCounter.append(_gs.frameCounter)
            
        data_dict = {}
        
        data_dict['listIndex'] = data_ind
        data_dict['frameCounter'] = data_frameCounter
        
        return data_dict

    @staticmethod
    def mergeDataDicts(*data_dicts):
        ret = {}
        for _dict in data_dicts:
            for _k in _dict.keys():
                ret[_k] = _dict[_k]
        return ret

    
    @staticmethod
    def columnOrder(df, first_cols):
        ''' return dataframe with new column order '''
    
        col_list = first_cols + [col for col in df.columns 
                             if col not in first_cols]
    
        _tmp_df = df[col_list]
    
        return _tmp_df

    
    @staticmethod
    def displayEvalMethodNames(list_str_names):
        ''' add a line carriage after each word'''
    
        list_ret = []
        
        for _name in list_str_names:
            
            ind_upper = map(lambda char: char.isupper(), _name)
            
            pos_upper = [x[0] for x in  
                filter(lambda tup_iv: tup_iv[1], enumerate(ind_upper))
                ]
            
            pos_upper.insert(0,0)
            pos_upper.append(len(_name))
            
            _ret = ""
            
            for i in range(len(pos_upper) - 1):
                
                _start = pos_upper[i]
                _end = pos_upper[i + 1]
                _ret += _name[_start: _end]
                _ret += "\n"
                
            list_ret.append(_ret)
            
        return list_ret