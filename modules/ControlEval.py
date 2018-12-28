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
from DataSchemas import  ScoreSchema
from EvalHelpers import EvalTracker, EvalDataset

class EvalFactory:

    ''' interfaces Eval Classes and calcs to work with the control-flow 
        logic of guiview 
    '''
    
    def __init__(self, on=False):
        self.on = on

        self.data = None

        self.data_pd = None
        
        self.evData = None
        self.ev = None
        
        self.currentInputScore = None
        self.currentTrackScore = None

        self._init()

    def isOn(self):
        return self.on

    def _init(self):
        ''' the true data init; but we return early if eval is off '''

        if not(self.on):
            return
        
        self.data = []
        
        self.evData = EvalDataset()
        self.ev = EvalTracker()

        self.currentInputScore = ScoreSchema()
        self.currentTrackScore = ScoreSchema()
        
        self.eval_method_names = [
            'checkBaselineInsideTrack',
            'checkBothContainsOther',
            'checkEitherContainsOther',
            'checkTrackInsideBaseline',
            'checkTrackInsideBaselineRect',
            'checkTrackSuccess',
            'compareRadii',
            'distanceFromBaseline'
            ]

    def checkExit(self):
        ''' allows us to exit from guiview loop'''
        if self.on:
            self.outputData()
            return True
        return False

    def setInputs(self
                 ,inputScore
                 ,trackScore
                 ):
        
        if inputScore is None:
            self.currentInputScore.reset()
        else:
            self.currentInputScore.load(inputScore)

        if trackScore is None:
            self.currentTrackScore.reset()
        else:
            self.currentTrackScore.load(trackScore)
        

    def _setInputScore(self, inputScore):
        ''' not implemented; jsut an idea'''
        pass

    def evalFrame(self, *args):

        list_data = []

        self.ev.setBaselineScore(self.currentInputScore.getAll())
    
        _trackScore = self.currentTrackScore.getAll()
        
        for meth_name in self.eval_method_names:

            try:
                _evMeth = getattr(self.ev, meth_name)
                _val = _evMeth(_trackScore)
            except:
                _val = None     #TODO pandas.nan ?
            
            list_data.append(_val)

        self.data.append(list_data)

    def outputData(self):

        data = copy.deepcopy(self.data)

        dict_data = {}
        
        for j_col in range(len(self.eval_method_names)):
            
            _tmp = []
            
            for i_row in range(len(data)):
            
                _tmp.append(data[i_row][j_col])
            
            dict_data[self.eval_method_names[j_col]] = _tmp
            
        self.data_pd = pd.DataFrame(dict_data)

        print self.data_pd[:10]

