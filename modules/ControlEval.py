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
import sqlalchemy


class EvalFactory:

    ''' interfaces Eval Classes and calcs to work with the control-flow 
        logic of guiview 
    '''
    
    def __init__(self, on=False, bProgressBar=True):
        self.on = on

        self.data = None
        self.data_pd = None

        self.db = None
        self.dbPathFn = None
        
        self.evData = None
        self.ev = None
        
        self.currentInputScore = None
        self.currentTrackScore = None

        self.bProgressBar = bProgressBar
        self.progressBarCounter = None
        self.progressBarMod = None
        self.progressBarWidth = None
        self.frameTotal = None

        self._init()

    def isOn(self):
        return self.on

    def _init(self):
        ''' the true data init; but we return early if eval is off '''

        if not(self.on):
            return
        
        print '\nSTART - running eval module...'

        if self.bProgressBar:
            
            self.progressBarCounter = 0
            self.progressBarMod = 30
            self.progressBarWidth = 30
            self.frameTotal = 0

            sys.stdout.write("[%s]" % (" " * self.progressBarWidth))
            sys.stdout.flush()
            sys.stdout.write("\b" * (self.progressBarWidth + 1))
        
        self.data = []
        
        self.dbPathFn = "data/usr/eval_tmp.db"
        self.db = DBInterface(self.dbPathFn)

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

    def updateByVid(self, frameTotal=None):
        
        if not(self.on):
            return
        
        if frameTotal is not None:
            if frameTotal > 0:
                
                self.frameTotal = frameTotal
        
                self.progressBarMod = int(self.frameTotal / self.progressBarWidth) + 1

        # TODO - add numbers to progress bar
        # https://stackoverflow.com/questions/3160699/python-progress-bar
                
        

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

    def progressBar(self):
        ''' update progress bar '''
        
        if not(self.bProgressBar):
            return
        
        if self.progressBarCounter % self.progressBarMod == 0:
            
            sys.stdout.write("-")
            sys.stdout.flush()

        self.progressBarCounter += 1



    def evalFrame(self, *args):

        list_data = []

        self.ev.setBaselineScore(self.currentInputScore.getAll())
    
        _trackScore = self.currentTrackScore.getAll()
        
        for meth_name in self.eval_method_names:

            try:
                _evMeth = getattr(self.ev, meth_name)
                _val = _evMeth(_trackScore)
            except:
                _val = None
            
            list_data.append(_val)

        self.data.append(list_data)

        self.progressBar()

    def outputData(self):

        data = copy.deepcopy(self.data)

        # data to form readable by pandas
        dict_data = {}
        
        for j_col in range(len(self.eval_method_names)):
            
            _tmp = []
            
            for i_row in range(len(data)):
            
                _tmp.append(data[i_row][j_col])
            
            dict_data[self.eval_method_names[j_col]] = _tmp
            
        # data to pandas
        self.data_pd = pd.DataFrame(dict_data)

        # output to db 
        engine = sqlalchemy.create_engine('sqlite:///' + self.dbPathFn
                                            ,echo=False)
        
        self.data_pd.to_sql('current_dataframe'
                            ,con = engine
                            ,if_exists='replace')

        sys.stdout.write("\n")
        print 'output db: %s' % str(self.dbPathFn)
        
        rows, cols = self.data_pd.shape
        print 'FINISH - rows: %s cols: % s ' % (str(rows), str(cols))

