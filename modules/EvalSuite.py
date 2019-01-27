import os, sys, copy, random, subprocess, time, math
import cv2
import numpy as np
import pandas as pd
import sqlalchemy
from matplotlib import pyplot as plt
from DataSchemas import ScoreSchema
from EvalHelpers import (EvalTracker, OutcomeData, AggEval, DFHelper)
from IPython.display import display


class EvalSuite:

    ''' Operate on and organize multiple DFClass types:
        
            OutcomeData, EvalTracker, AggEval

            - build all df types from a base dataset,
            - do logging and multiple ways
            - interface with master-db

    '''

    def __init__(self):
        
        self.outcomeModel = None
        self.aggModel = None

        self.evalTable = None
        
        self.outcomeDfh = None
        self.evalDfh = None
        self.aggDfh = None

    def buildFromOutcome(self, outcome_data_pd):
        ''' use outcome_data_df to build eval and agg tables; also
            create their dfhelper objects
        '''
        self.outcomeModel = OutcomeData(bLoad=False, bEval=False)
        self.outcomeModel.loads(outcome_data_pd)
        self.outcomeModel.eval()

        self.evalTable = self.outcomeModel.evalData.copy()
        
        self.aggModel = AggEval(self.evalTable)
        
        self.outcomeDfh = DFHelper(self.outcomeModel.outcomeData)
        self.evalDfh = DFHelper(self.evalTable)
        self.aggDfh = DFHelper(self.aggModel.getAggDf())

    def displayCli(self):
        ''' call from EvalFactory to print high-level stats on the run '''
        
        print ''
        self.outcomeModel.displaySummaryStats()   #TODO - print this when returns str
        print self.aggDfh.getAggEvalDisplay()

    def displayFullReport(self):
        ''' call this in jupyter for a large printout'''
        pass
        #TODO - outcomeData.displaySeriesPlots() / .displayDiameterPlot()

    def previewEachDf(self, clip_rows=3):
        ''' output each of the three main df's with formatting; 
            (helpful for first step when debugging)
            use clip_rows=0 for a full preview
        '''
        each_df_name = ('agg', 'eval', 'outcome')
        
        for df_name in each_df_name:

            if df_name == 'agg':
                _df = self.aggDfh.getAggEvalDisplay()
                print _df  # this is a string output

            if df_name == 'eval':
                _df = self.evalDfh.getDatasetDisplay()
                if clip_rows > 0:
                    _df = _df[:clip_rows]
                display(_df)
                
            if df_name == 'outcome':
                _df = self.outcomeDfh.getDatasetDisplay()
                if clip_rows > 0:
                    _df = _df[:clip_rows]
                display(_df)
