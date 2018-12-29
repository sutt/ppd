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

    # build properities ----------

    def propBaselineRadius(self):
        x, y, r = Display.rectToCircle(self.baselineScore[self.objEnum]['data'])
        return r

    # build calcs -----------------

    @staticmethod
    def calc_BallUnitsAway(df_main, df_props):
        return ( float(df_main['distanceFromBaseline']) / 
                 (float(df_props['propBaselineRadius']) * 2.0)  
                )





class EvalDataset:

    ''' put eval results into a dataframe '''

    def __init__(self):
        
        self.df = None

        self.df_props = None
        
        self.df_calcs = None

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

        self.eval_method_names_2 = [
            'checkBaselineInsideTrack',
            'checkBothContainsOther',
            'checkEitherContainsOther',
            # 'checkTrackInWindow',
            'checkTrackInsideBaseline',
            'checkTrackInsideBaselineRect',
            'checkTrackSuccess',
            'compareRadii',
            'distanceFromBaseline'
            ]

        self.prop_method_names = [
            'propBaselineRadius',
            ]

        self.calc_method_names = [
            'calc_BallUnitsAway',
            ]

        self.formatting_cols = {
            # 'checkBaselineInsideTrack':     '{:6.2f}',
            # 'checkBothContainsOther':       '{:6.2f}',
            # 'checkEitherContainsOther':     '{:6.2f}',
            # 'checkTrackInWindow':           '{:6.2f}',
            # 'checkTrackInsideBaseline':     '{:6.2f}',
            # 'checkTrackInsideBaselineRect': '{:6.2f}',
            # 'checkTrackSuccess':            '{:6.2f}',
            'compareRadii':                 '{:4.0f}',
            'distanceFromBaseline':         '{:4.0f}',
            'calc_BallUnitsAway':           '{:6.2f}'
            }
        
        self.col_order_default = [
             'listIndex'
            ,'frameCounter'
            ,'checkBothContainsOther'
            ,'distanceFromBaseline'
            ,'checkTrackSuccess'
            ]

        self.col_order_requested = None

        self.rows_requested = None

    def setDf(self, df):
        self.df = df
    
    def setFirstCols(self, list_first_cols):
        ''' for use before getDatasetDisplay; set to None to go back to default'''
        self.color_order_requested = copy.copy(list_first_cols)

    def getFirstCols(self):
        if self.col_order_requested is not None:
            return self.col_order_requested
        return self.col_order_default

    def setRowsRequested(self, psRows):
        ''' input: pandas series of booleans '''
        self.rows_requested = psRows

    def getFilteredIndex(self, filter_rows, return_index = "listIndex"):
        ''' returns field return_index for rows matching filter_rows '''
        _df = self.getDataset()
        _filtered = _df[filter_rows][return_index]
        return [int(x) for x in list(_filtered)]


    def buildDataset(self, listGS, tracker):
        ''' 
            input:  listGS - list of GuiveiwState objects
                    tracker - TrackFactory object, initialized
            
            Helper Function to build a table of eval performance data
            for multiple frames.

                rows corresponding to frames/gs's
                cols corresponding to EvalTracker properties
        '''

        eval_data = self.buildEvalData(listGS, tracker, self.eval_method_names_2)
        index_data = self.buildIndexData(listGS)
        full_data = self.mergeDataDicts(*[index_data, eval_data])
        
        df = pd.DataFrame(full_data)

        self.df = df

    def buildProps(self, listGS):
        ''' build properties dataframe '''

        #can we get framesize here?
            
        full_data = self.buildPropData(listGS, self.prop_method_names)

        self.df_props = pd.DataFrame(full_data)

    def buildCalcs(self):
        ''' build properties dataframe '''
            
        full_data = self.buildCalcData(self.calc_method_names)

        self.df_calcs = pd.DataFrame(full_data)

    
    def getDataset(self):
        return self.df

    def getFullDataset(self):
        all_dfs = [self.df, self.df_props, self.df_calcs]
        return pd.concat(all_dfs, axis = 1)

    
    def getDatasetDisplay(self, sort_args=None):
        ''' return.print  a dataframe with various formatting niceties'''

        # column order
        _df = self.df.copy()
        _df =  self.columnOrder(_df, first_cols = self.col_order_default)
        
        # column heading spacing
        _new_cols =  self.displayEvalMethodNames(_df.columns)
        _df.rename(columns = _new_cols, inplace=True)

        # filter rows
        if self.rows_requested is not None:
            _df = _df[self.rows_requested]

        # rounding / clipping, need to return on this line for
        # formatting to flow thru to jupyter
        return _df.style.format(self.new_col_formatting(_new_cols, self.formatting_cols))
    
    
    def calcRecord(self, record_index, method_names):

        list_data = []

        for meth_name in method_names:

            try:
                _ev = EvalTracker()
                _evMeth = getattr(_ev, meth_name)
                _val = _evMeth(  self.df[record_index: record_index+1]
                                ,self.df_props[record_index: record_index+1]
                                )
            except:
                _val = None
            
            list_data.append(_val)

        return list_data


    @staticmethod
    def propRecord(gs, method_names):
        ''' return a list of values (double, int, str, bool, obj) corresponding
            to the result an EvalTracker method for that gs. Order of list
            corresponds to order of method_names'''
        
        list_data = []

        try:
            _ev = EvalTracker()
            _ev.setBaselineScore(gs.displayInputScore)
            
        except:        
            return None
        
        for meth_name in method_names:

            try:
                _evMeth = getattr(_ev, meth_name)
                _val = _evMeth()
            except:
                _val = None
            
            list_data.append(_val)

        return list_data


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
    def buildPropData(cls, listGS, prop_method_names):
        
        data = []
        
        for _gs in listGS:
            
            _record = cls.propRecord(_gs, copy.copy(prop_method_names))
            
            data.append(_record)
            
        dict_data = {}
        
        for j_col in range(len(prop_method_names)):
            
            _tmp = []
            
            for i_row in range(len(data)):
            
                _tmp.append(data[i_row][j_col])
            
            dict_data[prop_method_names[j_col]] = _tmp
            
        return dict_data

    
    def buildCalcData(self, calc_method_names):
        
        data = []
        
        for _recordIndex in self.df.index:
            
            _record = self.calcRecord(_recordIndex, copy.copy(calc_method_names))
            
            data.append(_record)
            
        dict_data = {}
        
        for j_col in range(len(calc_method_names)):
            
            _tmp = []
            
            for i_row in range(len(data)):
            
                _tmp.append(data[i_row][j_col])
            
            dict_data[calc_method_names[j_col]] = _tmp
            
        return dict_data


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
    
        tmp_df = df[col_list]
    
        return tmp_df

    
    @staticmethod
    def new_col_formatting(dict_new_cols, dict_formatting):
        
        ret = {}

        for _k in dict_formatting.keys():
            ret[dict_new_cols[_k]] = dict_formatting[_k]

        return ret

    
    @staticmethod
    def displayEvalMethodNames(list_str_names):
        ''' add a line carriage after each word, corresponding to 
            first letter capitalization
            
            input: list_str_names - original column names (list of str)

            return: dict: 
                key - original col name (str)
                val - new col name (str)
            '''
    
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

        # pandas requires cols in dict format
        dict_ret = {}
        for _k, _v in zip(list_str_names, list_ret):
            dict_ret[str(_k)] = _v

        return dict_ret