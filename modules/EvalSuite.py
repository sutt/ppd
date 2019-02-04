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
        different tracking-algos on same data:
            
            current - the input / "most recent" eval run
            benchmark - the exisiting (best?) eval run on the same data

    '''
    
    def __init__(   self, 
                    benchmark_outcome_data=None,
                    current_outcome_data=None
                    ):
        
        self.benchmark  = EvalSuite()
        self.current    = EvalSuite()

        # comparison tables
        self.all_changes_df = None
        self.input_changes_df = None
        self.diff_eval_table = None
        

        if benchmark_outcome_data is not None:
            self.loadBenchmark(benchmark_outcome_data)

        if current_outcome_data is not None:
            self.loadCurrent(current_outcome_data)


    def loadBenchmark(self, benchmark_outcome_data):
        ''' load the benchmark table from master-db '''
        self.benchmark.buildFromOutcome(benchmark_outcome_data)

    def loadCurrent(self, current_outcome_data):
        self.current.buildFromOutcome(current_outcome_data)
    
    def diffAggTable(self, metrics=None, fields=None):
        ''' return a 3-section df: diff, current, benchmark 
            input:
                metrics - list of pandas agg function names e.g. ['mean']
                fields - list of  AggEval function names e.g. ['agg_checkTrackSucess']
        '''
        
        benchmark_df = self.benchmark.aggDfh.df.copy()
        current_df   = self.current.aggDfh.df.copy()

        if metrics is not None:
            benchmark_df = benchmark_df[metrics]
            current_df   = current_df[metrics]

        shared_table = self.diffDf(benchmark_df, current_df)

        if fields is not None:
            shared_table = shared_table.T[fields].T

        shared_table = shared_table.applymap('{:,.3f}'.format)

        return shared_table

    def diffAggFilterTable(self, metrics=None, fields=None):
        ''' return a 3-section df: diff, current, benchmark 
            input:
                metrics - list of pandas agg function names e.g. ['mean']
                fields - list of  AggEval function names e.g. ['agg_checkTrackSucess']
        '''
        
        benchmark_df = self.benchmark.aggFilterDfh.df.copy()
        current_df   = self.current.aggFilterDfh.df.copy()

        if metrics is not None:
            benchmark_df = benchmark_df[metrics]
            current_df   = current_df[metrics]

        shared_table = self.diffDf(benchmark_df, current_df)

        if fields is not None:
            shared_table = shared_table.T[fields].T

        try:
            shared_table = shared_table.applymap('{:,.3f}'.format)
        except Exception as e:
            print e
            # problem appears to be formatting apparent numeric columns that
            # are really str


        return shared_table

    def diffEvalTable(self, metrics=None, fields=None):
        ''' EvalTable with diff,current,benchmark-sections'''
        
        self.benchmark.evalDfh.setRowsRequested(s_cmd='inputframes')
        self.current.evalDfh.setRowsRequested(s_cmd='inputframes')
        
        benchmark_df = self.benchmark.evalDfh.getRows()
        current_df   = self.current.evalDfh.getRows()

        if metrics is not None:
            benchmark_df = benchmark_df[metrics]
            current_df   = current_df[metrics]

        shared_table = self.diffDf(benchmark_df, current_df)

        self.diff_eval_table = shared_table

        if fields is not None:
            shared_table = shared_table.T[fields].T

        try:
            shared_table.applymap('{:,.3f}'.format)
        except Exception as e:
            print e
            # problem appears to be formatting apparent numeric columns that
            # are really str

        return shared_table

    def inputFrameChanges(self, metrics=None, fields=None):
        ''' sample cmp-report'''

        #compare Agg Tables: Can this be universalized for aggFilter, etc...
        
        self.benchmark.evalDfh.setRowsRequested(s_cmd='inputframes')
        self.current.evalDfh.setRowsRequested(s_cmd='inputframes')
        
        benchmark_df = self.benchmark.evalDfh.getRows()
        current_df   = self.current.evalDfh.getRows()

        if metrics is not None:
            benchmark_df = benchmark_df[metrics]
            current_df   = current_df[metrics]

        d_diff = {}
        for _col in current_df.columns:
            d_diff[_col] = (current_df[_col].astype('float64') - 
                            benchmark_df[_col].astype('float64'))
        diff_df = pd.DataFrame(d_diff)

        changes_df = self.changesTable(diff_df)
        
        col_order = ['improvements', 'deprovements', 'sames']
        shared_table = changes_df[col_order]

        shared_table.applymap('{:,.3f}'.format)

        return shared_table

    
    def allFrameChanges(self, metrics=None, fields=None):
        ''' 
            build and return self.all_changes_df:
                rows - every metric in (allFrames) evalTable
                cols - improvement/regression/same on evalTable-metric

                (since input-data includes all frames, not just inputframes,
                 this is best for non input-frame comparisons, 
                 e.g. trackSuccess)

            args:
                metrics  - (list of str) filter for these from input-data
                fields   - (list of str) [not implemented] filter for these 
        '''
        
        self.benchmark.evalDfh.rows_requested = None
        self.current.evalDfh.rows_requested = None
        
        benchmark_df = self.benchmark.evalDfh.getRows()
        current_df   = self.current.evalDfh.getRows()

        if metrics is not None:
            benchmark_df = benchmark_df[metrics]
            current_df   = current_df[metrics]

        d_diff = {}
        for _col in current_df.columns:
            d_diff[_col] = (current_df[_col].astype('float64') - 
                            benchmark_df[_col].astype('float64'))

        diff_df = pd.DataFrame(d_diff)

        changes_df = self.changesTable(diff_df)

        self.all_changes_df = changes_df
        
        col_order = ['improvements', 'deprovements', 'sames']
        shared_table = changes_df[col_order]

        shared_table.applymap('{:,.3f}'.format)

        return shared_table

    @staticmethod
    def diffDf(benchmark_df, current_df):
        ''' 
            return diff_df, a dataframe,  with MultiIndex column:

                top-level-index:
                    'diff', 'current', 'benchmark'  (order specific)
                second-level-index:
                    <metric>, every column in input dataframes  (order undefined)

                row-index: shared index in input dataframes                
        '''

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

        return shared_table


    @staticmethod
    def changesTable(diff_df):
        ''' input: (pd.DataFrame) diff_df is an agg_metric(index) by a
            return (pd.DataFrame)
        '''

        EPSILON = 0.001

        def isImprovement(series_input):
            return series_input > EPSILON

        def isDeprovement(series_input):
            return series_input < - EPSILON

        def isSame(series_input):
            # use bitwse operators {~, &, | } for pd.Series
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

        return changes_df

    
    def plotTrackRadius(self, epsilon_offset = 3):
        '''
            plot two line graphs of trackRadius (Y) from current and benchmark algo
            across each frame-index (X)

                epsilon_offset: add this to one of the series so that the 
                                   lines don't overlay/occlude each other.

        '''

        col = 'propTrackRadius'
        current_radius = self.current.evalDfh.df[col]
        bench_radius = self.benchmark.evalDfh.df[col]

        #add this to make it more visible
        current_radius = [epsilon_offset + x for x in current_radius]

        data = zip(current_radius, bench_radius)
        plt.plot(data)
        plt.legend(['current + ' + str(epsilon_offset),'benchmark'])
        plt.title('Compare Track Radius')
        plt.show()

    
    def largestDiscrepancy(self, max_n = 20, **kwargs):
        ''' 
            for specified metric, return it sorted in descending order, w/
            frame indices 

                arg_name: argument name - grabs the metric of interest
                arg_val:  argument value - 
                    if positive, returns improvements
                    if negative, returns deproements
                    if zero, return both improve/deprove (absolute value)

                e.g: obj.largestDiscrepancy(checkTrackSuccess=1)
                    
                    returns:  <INSERT DF PRINTOUT HERE>

        '''
        
        # do we know to save / re-create the filters that counted improvements

        # this should include AND conditions for various requested metrics:
        # e.g. distance AND checkSuccess; might be too difficult
        
        if self.diff_eval_table is None:
            self.diffEvalTable()

        metric_distanceCurrentToBenchmark = kwargs.get('distanceCurrentToBenchmark', None)
        if metric_distanceCurrentToBenchmark is not None:
            data = 1
            self.diff_eval_table['distanceCurrentToBenchmark'] = data

        
        # perform operation on standard metrics
        ev = EvalTracker()
        eval_metrics = ev.getMethodNames()
        eval_metrics.extend(ev.getCalcNames)

        for _metric in eval_metrics:

            if _metric in kwargs.keys():

                arg_val = kwargs.get(_metric, None)

                if arg_val is None:
                    continue

                if arg_val == 0:

                    self.diff_eval_table()
        
        metric_checkTrackSuccess = kwargs.get('checkTrackSuccess', None)
        if metric_checkTrackSuccess is not None:
            pass
            # return improvements or deprovements?

        
        # sort a pandas table here:
        # self.all_changes_df.

    def getChanges(self,idk, **kwargs):
        pass
        # improvement / deprovement / same
        # how to get frame indices from these agg tables?
        kwargs.get('', None)

    def report1(self):

        #TODO - header
        # current - name?
        # benchmark - name or 'loaded
        
        display(self.allFrameChanges(
                    metrics=[
                        'checkTrackSuccess'
                        ]
                    )
                )

        display(self.inputFrameChanges(
                    metrics = [
                                'checkTrackSuccess',
                                'calcBaselineBallUnitsAway', 
                                'checkBothContainsOther',
                                'distanceFromBaseline'
                                ]
                    )
                )

        display(self.diffAggTable(
                    metrics=['mean'],
                    fields = [
                            'agg_checkTrackSuccess',
                            'agg_calcBaselineBallUnitsAway', 
                            'agg_checkBothContainsOther',
                            'agg_distanceFromBaseline'
                    ]
                    )
                )

        display(self.diffAggFilterTable(
                    metrics = None,  #['mean'],
                    fields = None
                    )
                )

        self.plotTrackRadius()

        #TODO - add largest discrepancy (by some metric)

if __name__ == "__main__":
    od = OutcomeData()
    suite = EvalSuite()
    suite.buildFromOutcome(od.getOutcome())
    suite.displayCli()