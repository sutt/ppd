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



class EvalFactory:

    ''' outputs inputScore and trackScore into sql for communication
        with next process;
        
        (this will run "silent" [self.on=False] many times within
         guiview so we construct it to do so lightly)
    '''
    
    def __init__(self, on=False, dbPathFn='', bProgressBar=True, bLog=False):
        ''' everything init to None; real init data is in _init() 
            where we can return before constructing heavy objects 
        '''

        self.on = on

        self.outcome_data = None
        self.outcome_data_pd = None

        self.db = None
        self.dbTblName = None
        self.dbPathFn = None
        
        if dbPathFn != "":
            self.dbPathFn = dbPathFn
        
        self.evData = None
        self.ev = None
        
        self.currentInputScore = None
        self.currentTrackScore = None

        self.bLog = bLog
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
            self.progressBarT0 = time.time()

            # this is looks better but doesn't work for subproc piping 
            # stdout with a variable seek
            # sys.stdout.write("[%s]" % (" " * self.progressBarWidth))
            # sys.stdout.flush()
            # sys.stdout.write("\b" * (self.progressBarWidth + 1))
            # sys.stdout.flush()
            sProgressBarTemplate = "["
            sProgressBarTemplate += " " * (self.progressBarWidth - 2)
            sProgressBarTemplate += "]\n"
            sys.stdout.write(sProgressBarTemplate)
            sys.stdout.flush()
        
        self.outcome_data = []
        
        self.dbTblName = 'outcome_dataframe'
        if self.dbPathFn is None:
            self.dbPathFn = "data/usr/eval_tmp.db"
        self.db = DBInterface(self.dbPathFn)

        self.evData = EvalDataset()
        self.ev = EvalTracker()

        self.currentInputScore = ScoreSchema()
        self.currentTrackScore = ScoreSchema()
        

    def checkExit(self):
        ''' allows us to exit from guiview loop'''
        if self.on:
            self.outputOutcomeData(bLog = self.bLog)
            return True
        return False

    def updateByVid(self, frameTotal=None):
        
        if not(self.on):
            return
        
        if frameTotal is not None:
            if frameTotal > 0:
                
                self.frameTotal = frameTotal
        
                self.progressBarMod = int(self.frameTotal / self.progressBarWidth) + 1
        

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
        

    def outcomeFrame(self, *args):
        ''' add outcome data to preserved data '''
        dict_data = {}
        dict_data['inputScore'] = copy.deepcopy(self.currentInputScore)
        dict_data['trackScore'] = copy.deepcopy(self.currentTrackScore)
        self.outcome_data.append(dict_data)
        self.progressBar()


    def outputOutcomeData(self, bLog=False):
        ''' take ScoreSchema obj's in outcome_data and output to a sql table

            field naming template:
                <type>_<field_name><field_num(opt)>_<objenum>

                    type: 'input' vs. 'track'
                    field_name: some string denoting what it means
                    field_num: (optional) to distinguish data scalars in a tuple
                    objenum: num corresponding to obj
        '''
        
        base_fields = ScoreSchema.getScalarFields(num_objs=4)
        
        all_fields = (str(_type) + '_' + str(_field)
                        for _field in base_fields 
                        for _type in ('input', 'track')
                        )
        full_data = {}
        for _field in all_fields:
            full_data[_field] = []
        
        for _record in copy.deepcopy(self.outcome_data):
            
            _typeDicts = []
            for _type in ('input', 'track'):

                try:
                
                    _typeKey = _type + 'Score'
                    _scoreObj = _record[_typeKey]

                    assert _scoreObj is not None
                    assert _scoreObj.__class__.__name__ == 'ScoreSchema'

                    _scalarsDictTmp = _scoreObj.toScalars()

                    _scalarsDict = {}
                    for _k in _scalarsDictTmp.keys():
                        _scalarsDict[str(_type) + '_' + str(_k)] = _scalarsDictTmp[_k]

                except:
                    _scalarsDict = {}

                _typeDicts.append(_scalarsDict)

            _recordDict = {}
            for _typeDict in _typeDicts:
                for _field in _typeDict:
                    _recordDict[_field] = _typeDict[_field]

            for _field in full_data:
                full_data[_field].append(
                    _recordDict.get(_field, None)
                )
            
        # data to pandas
        self.outcome_data_pd = pd.DataFrame(full_data)

        # output to db 
        engine = sqlalchemy.create_engine('sqlite:///' + self.dbPathFn
                                            ,echo=False)
        
        self.outcome_data_pd.to_sql(self.dbTblName
                            ,con = engine
                            ,if_exists='replace')

        # cli logging
        sys.stdout.write("\n")
        sys.stdout.flush()
        print 'output db: %s' % str(self.dbPathFn)

        rows, cols = self.outcome_data_pd.shape
        total_time = str(time.time() - self.progressBarT0)
        print 'output tbl: %s' % str(self.dbTblName)
        print 'eval time: %s' % total_time[:min(5, len(total_time) )]
        print 'FINISH - rows: %s cols: % s ' % (str(rows), str(cols))

        if bLog:

            outcomeData = OutcomeData(bLoad=False, bEval=False)
            outcomeData.loads(self.outcome_data_pd)
            outcomeData.eval()
            evalDf = outcomeData.evalData.copy()
            aggEval = AggEval(evalDf)
            aggDf = DFHelper(aggEval.getAggDf())

            print ''
            outcomeData.displaySummaryStats()
            print aggDf.getAggEvalDisplay()



    def progressBar(self):
        ''' update progress bar '''
        
        if not(self.bProgressBar):
            return
        
        if self.progressBarCounter % self.progressBarMod == 0:
            
            sys.stdout.write("-")
            sys.stdout.flush()

        self.progressBarCounter += 1
