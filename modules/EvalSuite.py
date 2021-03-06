import os, sys, copy, random, subprocess, time, math
import cv2
import numpy as np
import pandas as pd
import sqlalchemy
from matplotlib import pyplot as plt
from DataSchemas import ScoreSchema
from EvalHelpers import (EvalTracker, OutcomeData, AggEval, DFHelper)
from AnalysisHelpers import (subprocBatchOutput, compareTrackers)
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

        Terms:

            "Changes":each frame on each metric can be an:

                Improvement, Deprovement, Same

                same = diff is contained in (-epsilon, +epsilon) interval

                a changes_df is only for eval-tables, not agg-eval-tables.

                for all EvalTrack methods, "metrics", incr-value = incr-perf
                which helps us infer the sign of an improvement

            "Diff":   Diff = Current - Benchmark
            
                a diff_df is a dataframe with these threee sections as top index
                and an eval_metric (like checkTrackSuccess) or an agg_eval_metric
                like (agg_checkTrackSuccess) as second-level index


    '''
    
    def __init__(   self, 
                    benchmark_outcome_data=None,
                    current_outcome_data=None,
                    b_testing=False
                    ):
        
        self.benchmark  = EvalSuite()
        self.current    = EvalSuite()
        
        self.b_testing = b_testing     #suppress pyplot.show()

        # comparison tables
        self.all_changes_df = None
        self.input_changes_df = None
        self.diff_eval_table_input = None
        self.diff_eval_table_all = None
        

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

        shared_table = self.formatDf(shared_table)

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

        shared_table = self.formatDf(shared_table)

        return shared_table

    def diffEvalTable(self, metrics=None, fields=None, b_input_frames=True):
        ''' EvalTable with diff,current,benchmark-sections'''
        
        if b_input_frames:
            self.benchmark.evalDfh.setRowsRequested(s_cmd='inputframes')
            self.current.evalDfh.setRowsRequested(s_cmd='inputframes')
        else:
            self.benchmark.evalDfh.rows_requested = None
            self.current.evalDfh.rows_requested = None
        
        benchmark_df = self.benchmark.evalDfh.getRows()
        current_df   = self.current.evalDfh.getRows()

        if metrics is not None:
            benchmark_df = benchmark_df[metrics]
            current_df   = current_df[metrics]

        shared_table = self.diffDf(benchmark_df, current_df)

        if fields is not None:
            shared_table = shared_table.T[fields].T

        shared_table = self.formatDf(shared_table)

        if b_input_frames:
            self.diff_eval_table_input = shared_table
        else:
            self.diff_eval_table_all = shared_table

        return shared_table

    def inputFrameChanges(self, metrics=None, fields=None):
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
        
        self.benchmark.evalDfh.setRowsRequested(s_cmd='inputframes')
        self.current.evalDfh.setRowsRequested(s_cmd='inputframes')
        
        benchmark_df = self.benchmark.evalDfh.getRows()
        current_df   = self.current.evalDfh.getRows()

        if metrics is not None:
            benchmark_df = benchmark_df[metrics]
            current_df   = current_df[metrics]

        diff_df = self.diffDf(benchmark_df, current_df)

        changes_df = self.changesTable(diff_df['diff'])
        
        col_order = ['improvements', 'deprovements', 'sames']
        shared_table = changes_df[col_order]
        self.formatDf(shared_table)

        self.input_changes_df = shared_table
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

        diff_df = self.diffDf(benchmark_df, current_df)

        changes_df = self.changesTable(diff_df['diff'])
        
        col_order = ['improvements', 'deprovements', 'sames']
        shared_table = changes_df[col_order]
        shared_table = self.formatDf(shared_table)

        self.all_changes_df = shared_table

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

    
    @staticmethod
    def formatDf(df):
        ''' format df decimal output '''
        try:
            df = df.applymap('{:,.3f}'.format)
        except Exception as e:
            print e
        return df

    @staticmethod
    def distanceBetweenTracks(outcome_df_1, outcome_df_2
                             ,eval_dfh_1=None, eval_dfh_2=None):
        '''
            compare the distance b/w each algo's track-score at each frame

            input: 
                outcome_df_1 (df of class OutcomeData)  self.current.outcomeModel
                outcome_df_2 (df of class OutcomeData)  self.benchmark.outcomeModel
                eval_dfh_1   (df of class DFHelper)  self.current.evalDfh
                eval_dfh_2   (df of class DFHelper)  self.benchmark.evalDfh
        output:
            dict of list(s):  all elements are floats or Nones
                distanceList - distances (as negative) 
                radiusList   - avg-radius (as postives)  [optional]
                ballsAwayList - distance/radius (as negative) [optional]
        '''

        # validation + build loop-data
        assert outcome_df_1.__class__.__name__ == 'OutcomeData' 
        assert outcome_df_2.__class__.__name__ == 'OutcomeData'

        assert len(outcome_df_1.outcomeData) == len(outcome_df_1.outcomeData)

        try:
            assert outcome_df_1
        except:
            outcome_df_1.buildScoreSchemaList()
            outcome_df_2.buildScoreSchemaList()

        obj_list_1 = outcome_df_1.getScoreObjsList()
        obj_list_2 = outcome_df_2.getScoreObjsList()

        assert len(obj_list_1) == len(obj_list_2)
        
        # loop over all records, build distanceList    
        distanceList = []
        ev = EvalTracker()

        for _obj1, _obj2 in zip(obj_list_1, obj_list_2):

            track_score_1 = _obj1['track']
            track_score_2 = _obj2['track']
        
            ev.setBaselineScore(track_score_1)
            dist = ev.distanceFromBaseline(track_score_2)

            distanceList.append(dist)

        # build ballUnitsAway calculated field
        b_ballunits = False
        if (eval_dfh_1 is not None) and (eval_dfh_2 is not None):

            # validation
            assert eval_dfh_1.__class__.__name__ == 'DFHelper'
            assert eval_dfh_2.__class__.__name__ == 'DFHelper'
            
            b_ballunits = True

            radiusList = []
            ballsAwayList = []
            
            radius1 = eval_dfh_1.df['propTrackRadius']
            radius2 = eval_dfh_2.df['propTrackRadius']

            for _rad1, _rad2, _dist in zip(radius1, radius2, distanceList):

                _n = 2 - (int(math.isnan(_rad1)) + int(math.isnan(_rad2)))

                _summed = _rad1 + _rad2

                if _n == 0:
                    _avgradius = None
                else:
                    _avgradius = float(_summed) / float(_n)

                radiusList.append(_avgradius)

                if (_avgradius is not None) and (_dist is not None):
                    if not(math.isnan(_avgradius)) and not(math.isnan(_dist)):
                        
                        _ballsAway = float(_dist) / (float(_avgradius) * 2.0)
                    else:
                        _ballsAway = None
                else:
                    _ballsAway = None

                ballsAwayList.append(_ballsAway)
        
        return_dict = {}
        
        return_dict['distanceList'] = distanceList
        
        if b_ballunits:
            return_dict['radiusList'] = radiusList
            return_dict['ballsAwayList'] = ballsAwayList
        
        return return_dict

    def plotTrackDistance(self):
        '''
            plot two line graphs of the cartesian distance between baseline
            and current track_score. 
            across each frame-index (X), calculate (Y) by:
            a.) pixels,
            b.) "ball units" = pixel-distance / 2*avg_radius 
                    avg_radius = avg(baseline-radius, current-radius)
        '''

        series_dict = self.distanceBetweenTracks(
                                         self.current.outcomeModel
                                        ,self.benchmark.outcomeModel
                                        ,self.current.evalDfh
                                        ,self.benchmark.evalDfh
                                                 )
        
        def negOrNone(x):
            if x is None: 
                return None
            else:
                return -x
        
        series_pixel = [negOrNone(x) for x in series_dict['distanceList']]
        series_ballunits = [negOrNone(x) for x in series_dict['ballsAwayList']]
        
        fig, ax1 = plt.subplots()
        ax1.plot(series_pixel, color='b')
        ax1.set_ylabel('pixel distance')
        ax2 = ax1.twinx()
        ax2.plot(series_ballunits, color='r')
        ax2.set_ylabel('ball units')

        #TODO - finish formatting / dynamic elements
        # data = zip(series_pixel, series_ballunits)
        # plt.plot(series_pixel)
        # plt.legend(['pixel distance'])
        # plt.title('Compare Distance b/w Tracks')
        # plt.ylim(-1,20)
        ax1.set_ylim([0,20])
        ax2.set_ylim([0,6])
        if not(self.b_testing):
            plt.show()


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
        if not(self.b_testing):
            plt.show()

    
    def reportDiscrepancy(self 
                        ,metric_name
                        ,metric_val
                        ,vid_fn
                        ,current_algo
                        ,benchmark_algo
                        ,b_ret=False
                        ,max_display_n=5
                        ,max_plot_n=5 
                        ,**kwargs
                        ):
        '''
            calls to largestDiscrepancy and then performs comparison plot
            and displays report automatically

            input:
                metric_name - (str) name of eval metric to pass to largestDiscrep
                metric_val  - (int) value associated with metric_name
                vid_fn      - (str) path to video on which comparison is based
                current_algo - (obj) initialized tracker obj
                benchmark_algo - (obj) initialized tracker obj
                b_ret       - (bool) if True, return a dict of information
            
            return:
                dict of information if b_ret=True
        '''
        
        # call into func for sorted list
        args = {metric_name: metric_val}
        discrep_table = self.largestDiscrepancy(max_n=5, **args)
        
        num_rows = len(discrep_table)
        
        display(discrep_table[:min(num_rows,max_display_n)])

        foi_list = discrep_table.index[:min(num_rows, max_plot_n)]
        foi_list = [int(x) for x in foi_list]

        try:
            print 'runnning subprocBathcOutput, takes 5-30 seconds'
            tmpGS = subprocBatchOutput(
                                        f_pathfn=vid_fn
                                        ,batch_list=foi_list
                                        ,b_log=False
                                        )
        except Exception as e:
            print 'failed to run subprocBatchOutput on ', str(vid_fn)
            print 'err code: ', str(e)

        tmpGS.sort(key=lambda gs: foi_list.index(gs.frameCounter))
        
        listGS = copy.copy(tmpGS)

        listTrackers = [current_algo, benchmark_algo]

        compareTrackers(listGS, listTrackers, roiSelectFunc=True, expand_factor=1.0)

        if not(b_ret):
            return None
        
        ret = {}
        ret['discrep_table'] = discrep_table
        ret['foi_list'] = foi_list
        ret['listGS'] = listGS
        
        return ret



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
                returns:
                                diff           current         benchmark
                    checkTrackSuccess checkTrackSuccess checkTrackSuccess
                239               1.0              True             False
                232               1.0              True             False
                223               1.0              True             False

        '''
        
        # do we know to save / re-create the filters that counted improvements
        
        if self.diff_eval_table_all is None:
            self.diffEvalTable(b_input_frames=False)

        # custom metrics; don't exist within diff_eval_table_input
        # build these metrics into the diff_eval_table_input
        # they don't have a current+benchmark headers in their return table
        
        custom_metrics = ['distanceBetweenTracks', 'ballUnitsBetweenTracks']
        
        custom_metric = None
        for _cm in custom_metrics:
            if _cm in kwargs.keys():
                custom_metric = _cm
                break

        if custom_metric is not None:
        
            series_dict = self.distanceBetweenTracks(
                                         self.current.outcomeModel
                                        ,self.benchmark.outcomeModel
                                        ,self.current.evalDfh
                                        ,self.benchmark.evalDfh
                                                 )

            if custom_metric == 'distanceBetweenTracks':
                series_key = 'distanceList'
            if custom_metric == 'ballUnitsBetweenTracks':
                series_key = 'ballsAwayList'

            custom_series = pd.Series(series_dict[series_key])

            return_series = custom_series.sort_values(ascending=True)

            if max_n is not None:
                return_series = return_series[:max_n]

            return return_series


        # standard metrics - exist within diff_eval_table

        ev = EvalTracker()
        eval_metrics = ev.getMethodNames()
        eval_metrics.extend(ev.getCalcNames())
        #this should be equivalent to self.diff_eval_table_input.columns (w/o property fields)

        #improvements = positive-diffs, deprovements = negative-diffs

        for _metric in eval_metrics:

            if _metric in kwargs.keys():

                # match input arguments to valid columns
                
                arg_val = kwargs.get(_metric, None)

                if arg_val is None:
                    continue

                # field sort-style
                
                b_abs_value = False
                b_top_largest = True
                
                if arg_val == 0:            # look for greatest absolute value
                    b_abs_value = True
                    b_top_largest = True

                if arg_val > 0:             # look for improvements
                    b_abs_value = False
                    b_top_largest = True

                if arg_val < 0:             # look for deprovements
                    b_abs_value = False
                    b_top_largest = False

                
                pd.set_option('mode.chained_assignment', None)
                
                df_whole = self.diff_eval_table_all.copy()

                metric_col = _metric if not(b_abs_value) else 'abs_' + _metric

                df_diff = df_whole['diff']
                
                if b_abs_value:    
                    df_diff['abs_' + _metric] = df_diff[_metric].apply(abs)
                    
                df_sort = df_diff.sort_values(
                                            by=[metric_col]
                                            ,ascending=not(b_top_largest)
                                            )

                metric_ind = pd.MultiIndex.from_product(
                                    [['diff', 'current', 'benchmark'], [_metric]]
                                    )

                return_table = pd.DataFrame(df_whole[metric_ind], index = df_sort.index)

                return_table = self.formatDf(return_table)

                if max_n is not None:
                    return_table = return_table[:max_n]
                
                return return_table


    
    def getChanges(self, **kwargs):
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

        self.plotTrackDistance()

        #TODO - add largest discrepancy (by some metric)

if __name__ == "__main__":

    # od = OutcomeData()
    # suite = EvalSuite()
    # suite.buildFromOutcome(od.getOutcome())
    # suite.displayCli()

    db_path = 'data/misc/books/eval-report-3/'

    outcome_0 = OutcomeData(dbPathFn = db_path + 'algo_0.db')
    outcome_1 = OutcomeData(dbPathFn = db_path + 'algo_1.db')
    outcome_2 = OutcomeData(dbPathFn = db_path + 'algo_2.db')

    cmpA = CmpAlgoReport(benchmark_outcome_data = outcome_0.getOutcome(), 
                     current_outcome_data = outcome_2.getOutcome()
                    )

    discrep_ballsaway = cmpA.largestDiscrepancy(ballUnitsBetweenTracks=1, max_n=5)
    
    print discrep_ballsaway