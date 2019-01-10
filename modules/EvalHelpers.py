import sys, copy, random, subprocess, time
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



class EvalTracker:

    '''
        Different ways to evaluate if the ScoreSchema output from a trackFrame
        matches expectations.

        inputs are full scoring-dict, within this class we index the scoring-dict
        with 'objEnum' and 'data' keys

            e.g. EvalTracker.setBaselineScore(gs.displayInputScore)
                 (where gs.displayInputScore is a score-dict)

        Todo
        [ ] this only evals for type='circle'; not for type='ray'

    '''
    
    def __init__(self):
        self.baselineScore = None
        self.objEnum = '0'

    def setObjEnum(self, sObjEnum):
        self.objEnum = str(sObjEnum)

    def setBaselineScore(self, baselineScore):
        ''' input the data from a ScoreSchema, a nested dict '''
        try:
            assert type(baselineScore) is dict
        except:
            print 'baselineScore must be a dict'
            return
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

        # these are also calculated fields, but were designed
        # to work back to outcome data fields, largely
        # deprecated now.
        self.prop_method_names = [
            'propBaselineRadius',
            ]

        # these are 'calculated fields' - they operate on 
        # existing tbl fields
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



class OutcomeData:

    ''' for loading and manipulating the output of guiview --eval '''
    
    def __init__(self, 
                 dbPathFn='data/usr/eval_tmp.db',
                 tblName='outcome_dataframe',
                 bLoad=True,
                 bEval=True
                 ):

        self.outcomeData = None
        self.evalData = None

        self.listScoreObjs = []

        self.dbPathFn = dbPathFn
        self.tblName = tblName
        
        self.loaded=False
        self.loaded_ss=False
        
        if bLoad:
            self.load()

        if bEval:
            self.eval()

    def get(self):
        return self.outcomeData
    
    def load(self):
        ''' load data from db '''
        db_engine = sqlalchemy.create_engine('sqlite:///' + '../' + self.dbPathFn)
        self.outcomeData = pd.read_sql_table(self.tblName, con=db_engine)
        self.loaded=True

    def loads(self, outcome_df):
        ''' load data from data '''
        self.outcomeData = outcome_df.copy()
        self.loaded = True

    def eval(self):
        ''' apply eval methods to outcome dataframe '''
        data = None
        self.evalData = pd.DataFrame(data)

    def displayCondensedTable(self, objEnum=0):
        ''' display only cols for requested obj-enum
            display only rows for frame with an input-score
        '''
        rows = self.filterInputScoreRows(self.outcomeData, objEnum)
        cols = self.filterObjCols(self.outcomeData, objEnum)
        return self.outcomeData[rows][cols]

    def displaySummaryStats(self):

        NUM_OBJS = 6

        # build stats
        n = self.outcomeData.shape[0]
        
        objsScored = [i for i in range(NUM_OBJS) 
                        if any([elem == True for elem in 
                                self.outcomeData.get('input_obj_exists_' + str(i), [])]
                        )]
        
        objsTracked = [i for i in range(NUM_OBJS) 
                        if any([elem == True for elem in 
                                self.outcomeData.get('track_obj_exists_' + str(i), [])]
                        )]

        inputIndices = [[i for i,v in enumerate(
                                    self.outcomeData['input_obj_exists_' + str(obj_enum)] 
                                    ) if v == True]
                        for obj_enum in objsScored]
        
        inputIndices = list(reduce(lambda a,b: set.union(set(a), set(b)), inputIndices))

        numInputs = len(inputIndices)

        
        # format stats
        _n = str(n)
        _objsScored = ",".join([str(elem) for elem in objsScored])
        _objsTracked = ",".join([str(elem) for elem in objsTracked])

        inputIndices.sort()
        _inputIndices = [str(elem) for elem in inputIndices]
        _max_lo, _max_hi = min(len(inputIndices), 3), max(min(len(inputIndices) - 3, 3), 0)
        _inputIndices = (','.join(_inputIndices[:_max_lo]) + 
                         ('' if _max_hi == 0 else 
                          '...' + ','.join(_inputIndices[-_max_hi:])
                         ))
        _numInputs = str(numInputs)
        
        
        print 'num frames:                  %s'          %  _n
        print 'obj enums scored/tracked:    %s / %s'     % (_objsScored, _objsTracked)
        print 'num scored frames:           %s | %s'     % (_numInputs, _inputIndices)
        
        print '-------'
        
        # other stats? - this won't include eval data yet


    def displaySeriesPlot(self, col_names=None, calc_fields=None, obj_legend=None
                                ,chart_title=None):
        ''' plot of the specified series; either col_names or calc_fields is not None

            col_names   - None, str, list-of-str
                            plot the column names specified; auto created legend
            calc_fields - None, list-of-list-of-value_data(int/float)
                            plot the fields data passed-in; req's obj_legend for legend
            obj_legend  - None, list-of-str
                            list of series titles

            examples:

                displaySeriesPlot(col_names=['obj_exists_0'])
                
                displaySeriesPlot(calc_fields=[[1,2,3], [1,0,1]], obj_legend=['a','b'])
        '''
        if col_names is not None:
            
            for _col in col_names:
                plt.plot(self.outcomeData[_col])
            
            if obj_legend is None:
                
                plt.legend(col_names)

        if calc_fields is not None:
            
            for _field in calc_fields:
                
                if type(_field) is list:
                    plt.plot(_field)

                elif type(_field) is dict:
                    xkeys = [_k for _k in _field.keys()]
                    xkeys.sort()
                    yvals = [_field[_k] for _k in xkeys]
                    plt.scatter(xkeys, yvals, c='orange')
        
            if obj_legend is not None:
                plt.legend(obj_legend)

        if chart_title is not None:
            plt.title(chart_title)

        plt.show()

    def displayDiameterPlot(self, objEnum=0, b_ret=False):
        ''' runs a preconfigured comparison plot and returns the raw data
            compares the diameter of track vs input
                note: diameter is minimum of enclosing rect dimensions
        
        build allData as such:
            {
                True: {
                         'input':  (  [series1_x1, series1_x2, ...]
                                    ,[series1_y1, series1_y2, ...]
                                )
                        
                         'track': (  [series2_x1, series2_x2, ...]
                                    ,[series2_y1, series2_y2, ...]
                                )
                        }
                False:   [same as above]
                    ...
            }
        '''
        
        allData = {}
        allLegend = {}
        
        # build data
        for _allFrames in (True, False):
            
            data, legend = {}, {}
            
            if _allFrames:

                df = self.outcomeData
                x_index = list(df.index)

            else:

                ind = self.filterInputScoreRows(self.outcomeData, objEnum=objEnum)
                df = self.outcomeData[ind]
                x_index = [i for i,v in enumerate(ind) if v==True]
                
                
            for _type in ('input', 'track'):
                
                _fields =  [_type + '_' + elem + '_' + str(objEnum) 
                            for elem in ('data2', 'data3')
                        ]
                
                _series = [min(a,b) for a,b in zip(  list(df[_fields[0]])
                                                    ,list(df[_fields[1]])
                                    )]
                
                data[_type] = (x_index, _series)
                
                legend[_type] = (_type)

            allData[_allFrames] = data

        if b_ret:
            return allData    

        # plotting
        for _allFrames in allData.keys():
            
            _plotData = allData[_allFrames]
            _plotLegend = []

            for _series in _plotData.keys():
            
                x, y = _plotData[_series][0], _plotData[_series][1]
                
                _marker = None
                if not(_allFrames): _marker = 'o'

                _plotLegend.append(str(_series))

                if (_allFrames == True) and (_series == 'input'):
                    plt.scatter(x, y, c='orange')
                else:
                    plt.plot(x, y, marker=_marker)

            # formatting
            _title = 'All Frames' if _allFrames else 'Frames with Input Score'
            plt.title(_title)
            plt.ylabel('ball diameter')
            plt.legend(_plotLegend)

            plt.show()


    @staticmethod
    def filterObjCols(df, objEnum=0):
        obj_cols = filter(lambda sCol: sCol.find('_' + str(objEnum)) > -1, 
                     list(df.columns))
        return obj_cols

    @staticmethod
    def filterInputScoreRows(df, objEnum=0):
        col_name = 'input_obj_exists_' + str(objEnum)
        filtered_rows = df[col_name] == True
        return filtered_rows

    
    def buildScoreSchemaList(self):
        ''' populate a ScoreSchema object(s) for each record in outcome dataframe;
            add to a dict (for input vs track), add that to a list. 
            scoreObjList:
                [   {'input':SS, 'track':SS }   <record0>
                    {'input':SS, 'track':SS }   <record1>
                     ...
                ]
        '''

        def modKey(s):
            # remove extraneous char's from keys
            # 'input_data0_1' -> 'data0'
            s = s.replace('track', '')
            s = s.replace('input', '')
            ind = s[::-1].index('_') + 1
            if ind > 0:
                s = s[:-ind]
            s = s.replace('_', '')
            return s    

        def sepTypeData(fulldata):
            # separate the fields into 'track' vs 'input'
            # {name1: val1, ...}  (full record as a dict)   -> 
            # {'track':{name1:val1,...}, 'input':{name2:val2,...}}
            sep_scalars = {}
            for _type in ('input', 'track'):
                _tmp = {}
                for _key in fulldata:
                    if _type in _key:
                        _tmp[_key] = fulldata[_key]
                sep_scalars[_type] = copy.deepcopy(_tmp)
            return sep_scalars
        
        def enumFromStr(s):
            # parse the field name string, return int for obj enum
            # return None for failed parse
            try:
                ind = s[::-1].index('_')
                ret = int(s[-ind:])
                return ret
            except:
                return None

        def sepObjData(record_dict):
            # separate data into indv obj's; eliminate un-used objects
            # {name1_0:val, name1_1:val ...} ->
            # {'0': {name1_0:val, ...}, '1': {name1_1:val, ...}, ...}
            mod_dict = {}
            for _typeKey in record_dict.keys():
                obj_dict = {}
                for _fieldKey in record_dict[_typeKey].keys():
                    enum = enumFromStr(_fieldKey)
                    if enum is not None:
                        
                        #TODO - check obj_exists_I value before proceeding?
                        
                        val = record_dict[_typeKey][_fieldKey]
                        
                        if str(enum) not in obj_dict.keys():
                            obj_dict[str(enum)] = {_fieldKey: val}
                        else:
                            obj_dict[str(enum)][_fieldKey] = val
                mod_dict[_typeKey] = obj_dict
            return mod_dict

        def modKeyData(record_dict):
            # apply modKey to each key in the dict; replace old key; leave 
            # values unchanged
            for _typeKey in record_dict.keys():
                for _objKey in record_dict[_typeKey].keys():
                    for _fieldKey in record_dict[_typeKey][_objKey].keys():
                        newKey = modKey(_fieldKey)
                        record_dict[_typeKey][_objKey][newKey] = (
                            record_dict[_typeKey][_objKey].pop(_fieldKey)
                            )
            return record_dict


        # list of dicts; dict representing record
        # 1: k/v
        dRecords = self.outcomeData.to_dict(orient='record')
        
        # list of dict of dict. nest_level:
        # 1: type
        # 2: k/v
        dRecords_nest_1 = map(lambda _dr: sepTypeData(_dr), dRecords)

        # list of dict of dict of dict. nest level:
        # 1: type
        # 2: obj_enum
        # 3: k/v
        dRecords_nest_2 = map(lambda _dr: sepObjData(_dr), dRecords_nest_1)
        
        # list of dict of dict of dict. nest level:
        # 1: type
        # 2: obj_enum
        # 3: k_mod/v
        dRecords_nest_2_mod = map(lambda _dr: modKeyData(_dr), dRecords_nest_2)

        # build listScoreObjs: list of dict of dict
        # 1: list of records
        # 2: dict of type
        # 3: dict from scoreschema.data [ret from .getAll()]
        for _record in dRecords_nest_2_mod:

            _tmp = {}

            for _type in _record.keys():    
                
                _ss = ScoreSchema()

                for _objEnum in _record[_type].keys():     
                    
                    try:
            
                        kv = _record[_type][_objEnum]
                        
                        assert type(kv) is dict

                        assert kv['objexists']
                    
                        _ss.fromScalarsAddObject(objEnum=_objEnum, **kv)
                    
                    except:
                        pass

                _tmp[_type] = _ss.getAll()

            self.listScoreObjs.append(_tmp)

        # validate
        assert len(self.listScoreObjs) == len(self.outcomeData)
        self.loaded_ss = True
                

    
if __name__ == "__main__":
    # pass
    od = OutcomeData()
    od.buildScoreSchemaList()
