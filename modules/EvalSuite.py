import sys, copy, random, subprocess, time
import pickle
import sqlalchemy
import cv2
import numpy as np
import io
import pandas as pd
from PIL import Image
from collections import OrderedDict
from itertools import combinations
from Interproc import DBInterface
from Interproc import GuiviewState
from ControlTracking import TrackFactory
from ControlDisplay import Display
from DataSchemas import  ScoreSchema
from EvalHelpers import EvalTracker, EvalDataset
from EvalHelpers import OutcomeData, AggEval, DFHelper

import os, sys, copy, random, subprocess, time, math
import pickle
import cv2
import numpy as np
import io
import pandas as pd
import sqlalchemy
from PIL import Image
from collections import OrderedDict
from itertools import combinations
from Interproc import DBInterface
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from Interproc import GuiviewState
from ControlTracking import TrackFactory
from ControlDisplay import Display
from DataSchemas import ScoreSchema

from IPython.display import display



class EvalSuite:

    ''' operate on and organize multiple DFClass types:
        
            OutcomeData, AggEval, EvalData?

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
        self.outcomeModel.displaySummaryStats()
        print self.aggDfh.getAggEvalDisplay()

    def displayFullReport(self):
        ''' call this in jupyter for a large printout'''
        pass

    def previewEachDf(self):
        ''' output a couple rows from each of the three main df's
            with formatting; helpful for first step when debugging
        '''
        each_df_name = ('agg', 'eval', 'outcome')
        
        for df_name in each_df_name:

            if df_name == 'agg':
                display(self.aggModel.getAggDf()[:3])

            if df_name == 'eval':
                display(self.evalDfh.getDatasetDisplay()[:3])
                
            if df_name == 'outcome':
                display(self.outcomeDfh.getDatasetDisplay()[:3])
