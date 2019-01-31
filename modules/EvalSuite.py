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
        self.aggFilterDfh = None

        self.default_agg_cols = [
                                'agg_calcBaselineBallUnitsAway', 
                                'agg_checkBothContainsOther',
                                'agg_checkTrackSuccess',
                                'fagg_less_than_20_pix_balls_away',
                                'fagg_less_than_30_pix_success'
                                ]

    def buildFromOutcome(self, outcome_data_pd):
        ''' use outcome_data_df to build eval and agg tables; also
            create their dfhelper objects
        '''
        self.outcomeModel = OutcomeData(bLoad=False, bEval=False)
        self.outcomeModel.loads(outcome_data_pd)
        self.outcomeModel.eval()

        self.evalTable = self.outcomeModel.getEval()
        
        self.aggModel = AggEval(self.evalTable)
        
        self.outcomeDfh = DFHelper(self.outcomeModel.getOutcome())
        self.evalDfh = DFHelper(self.evalTable)
        self.aggDfh = DFHelper(self.aggModel.getAggDf())
        self.aggFilterDfh = DFHelper(self.aggModel.getFilteredAggDf())

    def displayCli(self):
        ''' call from EvalFactory to print high-level stats on the run '''
        
        print ''
        print self.outcomeModel.displaySummaryStats()

        print DFHelper.toStringFormatOutput(
                self.aggDfh.getAggEvalDisplay(metrics_requested=self.default_agg_cols)
                )
        
        print DFHelper.toStringFormatOutput(
                self.aggFilterDfh.getAggEvalDisplay(metrics_requested=self.default_agg_cols)
                )
        
        print '-----'

    def displayFullReport(self):
        ''' call this in jupyter for a large printout'''
        
        print 'video / metalog information \n'
        #TODO - video name
        print self.outcomeModel.displaySummaryStats()
        
        print '\nselect aggregates \n'
        display(self.aggDfh.getAggEvalDisplay(
                        metrics_requested=self.default_agg_cols)
                )
        display(self.aggFilterDfh.getAggFilterDisplay(
                        metrics_requested=self.default_agg_cols)
                )
        
        print 'plotting radius comparison \n'
        self.outcomeModel.displayDiameterPlot()
        
        print '\nfull eval table on input frames \n'
        self.evalDfh.setRowsRequested(s_cmd='inputframes')
        display(self.evalDfh.getDatasetDisplay())

        print '\na preview of each eval dataframe'
        self.previewEachDf()



    def previewEachDf(self, clip_rows=3):
        ''' output each of the three main df's with formatting; 
            (helpful for first step when debugging)
            use clip_rows=0 for a full preview
        '''
        each_df_name = ('agg', 'eval', 'outcome')
        
        for df_name in each_df_name:

            if df_name == 'agg':
                _df = self.aggDfh.getAggEvalDisplay()
                if clip_rows > 0:
                    _df = _df[:clip_rows]
                display(_df)

                _df = self.aggFilterDfh.getAggFilterDisplay()
                if clip_rows > 0:
                    _df = _df[:clip_rows]
                display(_df)

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


class CmpAlgoReport:

    ''' a report that compares the difference between two
        different tracking-algos:
            
            current - the input / "most recent" eval run
            benchmark - the exisiting (best?) eval run on the same data

        

    '''
    
    def __init__(   self, 
                    benchmark_outcome_data=None,
                    current_outcome_data=None
                    ):
        
        self.benchmark  = EvalSuite()
        self.current    = EvalSuite()

        if benchmark_outcome_data is not None:
            self.loadBenchmark(benchmark_outcome_data)

        if current_outcome_data is not None:
            self.loadCurrent(current_outcome_data)


    def loadBenchmark(self, benchmark_outcome_data):
        ''' load the benchmark table from master-db '''
        self.benchmark.buildFromOutcome(benchmark_outcome_data)

    def loadCurrent(self, current_outcome_data):
        self.current.buildFromOutcome(current_outcome_data)
    
    def basic(self, metrics=None, fields=None):
        ''' sample cmp-report'''

        #compare Agg Tables: Can this be universalized for aggFilter, etc...
        
        benchmark_df = self.benchmark.aggDfh.df.copy()
        current_df   = self.current.aggDfh.df.copy()

        if metrics is not None:
            benchmark_df = benchmark_df[metrics]
            current_df   = current_df[metrics]

        diff_values = current_df.values - benchmark_df.values
        diff_df = pd.DataFrame( diff_values
                                ,columns=current_df.columns
                                ,index=current_df.index)
        
        
        col_order = ['diff','current', 'benchmark']
        d_tmp = {
                 'diff':      diff_df
                ,'current':   current_df
                ,'benchmark': benchmark_df
                }

        keys, values = zip(*d_tmp.items())

        shared_table = pd.concat(values, keys=keys, axis=1)
        shared_table = shared_table[col_order]

        if fields is not None:
            shared_table = shared_table[fields]

        shared_table = shared_table.applymap('{:,.3f}'.format)

        return shared_table

    def basic2(self, metrics=None, fields=None):
        ''' sample cmp-report'''

        #compare Agg Tables: Can this be universalized for aggFilter, etc...
        
        self.benchmark.evalDfh.setRowsRequested(s_cmd='inputframes')
        self.current.evalDfh.setRowsRequested(s_cmd='inputframes')
        
        benchmark_df = self.benchmark.evalDfh.getDatasetDisplay()
        current_df   = self.current.evalDfh.getDatasetDisplay()

        if metrics is not None:
            benchmark_df = benchmark_df[metrics]
            current_df   = current_df[metrics]

        d_diff = {}
        for _col in current_df.columns:
            # note: convert everything to float to evaluate minus operator
            #       on all types of data: float, int, bool, etc.
            #       None should be converted to NaN
            d_diff[_col] = (current_df[_col].astype('float64') - 
                            benchmark_df[_col].astype('float64'))

        diff_df = pd.DataFrame(d_diff)

        col_order = ['diff','current', 'benchmark']
        
        d_tmp = {
                 'diff':      diff_df
                ,'current':   current_df
                ,'benchmark': benchmark_df
                }

        keys, values = zip(*d_tmp.items())

        shared_table = pd.concat(values, keys=keys, axis=1)
        shared_table = shared_table[col_order]

        if fields is not None:
            shared_table = shared_table[fields]

        # shared_table.applymap('{:,.3f}'.format)

        return shared_table

    def basic3(self, metrics=None, fields=None):
        ''' sample cmp-report'''

        #compare Agg Tables: Can this be universalized for aggFilter, etc...
        
        self.benchmark.evalDfh.setRowsRequested(s_cmd='inputframes')
        self.current.evalDfh.setRowsRequested(s_cmd='inputframes')
        
        benchmark_df = self.benchmark.evalDfh.getDatasetDisplay()
        current_df   = self.current.evalDfh.getDatasetDisplay()

        if metrics is not None:
            benchmark_df = benchmark_df[metrics]
            current_df   = current_df[metrics]

        d_diff = {}
        for _col in current_df.columns:
            d_diff[_col] = (current_df[_col].astype('float64') - 
                            benchmark_df[_col].astype('float64'))

        diff_df = pd.DataFrame(d_diff)

        
        EPSILON = 0.001

        def isImprovement(series_input):
            return series_input > EPSILON

        def isDeprovement(series_input):
            return series_input < - EPSILON

        def isSame(series_input):
            #note: use bitwse operators {~, &, | } for pd.Series
            return ~(series_input > EPSILON) & ~(series_input < -EPSILON)
        
        improve_df = diff_df.apply(isImprovement).sum()
        deprove_df = diff_df.apply(isDeprovement).sum()
        same_df    = diff_df.apply(isSame).sum()

        col_order = ['diff','current', 'benchmark']
        
        d_tmp = {'improvements': improve_df,
                'deprovements': deprove_df,
                'sames':        same_df}

        changes_df = pd.concat(d_tmp.values(), keys = d_tmp.keys())
        
        changes_df = changes_df.swaplevel(-1, -2)

        changes_df = changes_df.unstack()
        
        # changes_df = changes_df.T
        
        col_order = ['improvements', 'deprovements', 'sames']
        shared_table = changes_df[col_order]

        # shared_table.applymap('{:,.3f}'.format)

        return shared_table



        


if __name__ == "__main__":
    od = OutcomeData()
    suite = EvalSuite()
    suite.buildFromOutcome(od.getOutcome())
    suite.displayCli()