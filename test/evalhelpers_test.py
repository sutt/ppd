import os, sys, json, copy, math, pickle
import pandas as pd
import numpy as np
from utils import listContainSameElems, diff_pd
sys.path.append("../")
from modules.DataSchemas import ScoreSchema
from modules.ControlTracking import TrackFactory
from modules.Interproc import DBInterface, GuiviewState
from modules.EvalHelpers import EvalTracker, EvalDataset, OutcomeData, DFHelper

def test_OutcomeData_buildScoreSchemaList():
    
    path_test = '''data/test/evalhelpers/buildScoreSchemaList/'''
    
    path_db = os.path.join(path_test, 'eval_tmp.db')
    path_answer = os.path.join('..', path_test, 'answer.json')
    
    od = OutcomeData(dbPathFn=path_db, bLoad=True)
    od.buildScoreSchemaList()
    ret_data = od.listScoreObjs
    
    # this is pre-calculated result; we'll be able to catch deviations
    # by comparing against this test run's result
    ANSWER = json.load(open(path_answer, 'r'))

    # assert the two objects are the same
    assert cmp(ret_data, ANSWER) == 0

    # induce mismatch; verify cmp() identifies discrepancy
    ANSWER.pop()
    assert cmp(ret_data, ANSWER) != 0

def test_outcomeData_eval():

    path_test = '''data/test/evalhelpers/eval/'''
    
    path_db = os.path.join(path_test, 'eval_tmp.db')
    path_answer = os.path.join('..', path_test, 'answer.pickle')
    path_tmpdf = os.path.join('..', path_test, 'tmp.pickle')

    od = OutcomeData(dbPathFn=path_db, bLoad=True, bEval=True)
    ret_data = od.evalData

    # into/out of pickle to match the slight formatting changes
    # that also occured to answer.pickle
    ret_data.to_pickle(path_tmpdf)
    incoming_df = pd.read_pickle(path_tmpdf)

    answer_df = pd.read_pickle(path_answer)

    # note: can't cmp nan's, so right now the these equivalent dicts fail
    # we need to remove nan before we can do a comprehensive cmp() of 
    # these elements
    d1 = incoming_df.to_dict()
    d2 = answer_df.to_dict()

    # right now, test for certain properties, later for each data element
    assert (incoming_df.shape == answer_df.shape)
    assert all(map(lambda col: col in answer_df.columns, incoming_df.columns))

    assert cmp(incoming_df[0:1].to_dict(), answer_df[0:1].to_dict()) == 0

    ANSWER = '''num frames:                  383 \nobj enums scored/tracked:    0,1 / 0 \nnum scored frames:           10 | 0,22,40...125,188,380 \n-------'''
    assert od.displaySummaryStats() == ANSWER


def test_EvalTracker_eval_methods_good():

    ev = EvalTracker()
    
    assert ev.getMethodNames() == [
            'checkBaselineInsideTrack',
            'checkBothContainsOther',
            'checkEitherContainsOther',
            'checkTrackInsideBaseline',
            'checkTrackInsideBaselineRect',
            'checkTrackSuccess',
            'compareRadii',
            'distanceFromBaseline'
            ]

    # test perfect match
    inputScore = {'0':{'type':'circle','data':[10,10,5,5] } }
    trackScore = {'0':{'type':'circle','data':[10,10,5,5] } }
    ev.setBaselineScore(inputScore)

    list_data = []
    for meth_name in copy.copy(ev.eval_method_names):
        try:
            evMeth = getattr(ev, meth_name)
            val = evMeth(trackScore)
        except:
            val = 'exception'
        list_data.append(val)

    ANSWER = [True, True, True, True, False, True, 0, 0.0]
    assert list_data == ANSWER


    # test small diff
    inputScore = {'0':{'type':'circle','data':[10,10,5,5] } }
    trackScore = {'0':{'type':'circle','data':[12,11,6,7] } }

    ev.setBaselineScore(inputScore)

    list_data = []
    for meth_name in copy.copy(ev.eval_method_names):
        try:
            evMeth = getattr(ev, meth_name)
            val = evMeth(trackScore)
        except:
            val = 'exception'
        list_data.append(val)

    ANSWER = [True, True, True, True, True, True, 1, -3.605551275463989]
    assert list_data == ANSWER


def test_EvalTracker_eval_methods_good_2():

    ev = EvalTracker()
    
    # test bad trackScore
    inputScore = {'0':{'type':'circle','data':[10,10,5,5] } }
    trackScore = {'1':{'type':'circle','data':[10,10,5,5] } }
    ev.setBaselineScore(inputScore)

    list_data = []
    for meth_name in copy.copy(ev.eval_method_names):
        try:
            evMeth = getattr(ev, meth_name)
            val = evMeth(trackScore)
        except:
            val = 'exception'
        list_data.append(val)

    ANSWER = [None, None, None, None, None, False, None, None]
    assert list_data == ANSWER


    # test bad trackScore with changed naReturn val
    inputScore = {'0':{'type':'circle','data':[10,10,5,5] } }
    trackScore = {'1':{'type':'circle','data':[10,10,5,5] } }
    ev.setBaselineScore(inputScore)
    ev.setNaReturn(np.NaN)

    list_data = []
    names = copy.copy(ev.eval_method_names)
    names.pop(ev.eval_method_names.index('checkTrackSuccess'))
    for meth_name in names:
        try:
            evMeth = getattr(ev, meth_name)
            val = evMeth(trackScore)
        except:
            val = 'exception'
        list_data.append(val)

    assert all(map(math.isnan, list_data))


def test_EvalTracker_setBaseline_bad():

    ev = EvalTracker()
    
    # show it works with good score
    good_score = {'0':{'type':'circle','data':[10,10,5,5] } }
    ev.setBaselineScore(good_score)
    assert ev.baselineScore == good_score
    assert ev._validateParams() == True

    # show it fails with bad score: no type
    bad_score = {'0':{'blah':'circle','data':[10,10,5,5] } }
    ev.setBaselineScore(bad_score)
    assert ev.baselineScore is None
    assert ev._validateParams() == False

    # show it fails with bad score: score is none
    bad_score = None
    ev.setBaselineScore(bad_score)
    assert ev.baselineScore is None
    assert ev._validateParams() == False

    # show it fails with bad score: blank dict
    bad_score = {}
    ev.setBaselineScore(bad_score)
    assert ev.baselineScore == {}
    assert ev._validateParams() == False

def test_EvalTracker_validateParams():

    ev = EvalTracker()

    good_score = {'0':{'type':'circle','data':[10,10,5,5] } }
    ev.setBaselineScore(good_score)    
    
    #works
    ev.setObjEnum('0')
    assert ev._validateParams() == True

    #fails
    ev.setObjEnum('1')
    assert ev._validateParams() == False

    #fails
    track_score = {'1':{'type':'circle','data':[10,10,5,5] } }
    ev.setObjEnum('0')
    assert ev._validateParams(track_score) == False

def test_DFHelper_displayEvalMethodNames():

    # for capitalized
    dfh = DFHelper()
    
    names_input = ['checkBaselineInside']
    output = dfh.displayEvalMethodNames(names_input)
    ANSWER = {'checkBaselineInside':'check\nBaseline\nInside\n'}
    assert ANSWER == output

    names_input = ['checkBaselineInside', 'track_input_data0_1']
    output = dfh.displayEvalMethodNames(names_input, b_underscore=True)
    ANSWER = {'checkBaselineInside':'check\nBaseline\nInside\n',
              'track_input_data0_1':'track\n_input\n_data0\n_1\n'}
    assert ANSWER == output

def test_OutcomeData_displayDiameterPlot():
    
    path_test = '''data/test/evalhelpers/displayDiameterPlot/'''
    
    path_db = os.path.join(path_test, 'eval_tmp.db')
    path_answer = os.path.join('..', path_test, 'answer.json')

    od = OutcomeData(path_db)
    output = od.displayDiameterPlot(b_ret=True)

    nan = np.NaN
    def nar(list_vals):
        # NAReplace: replace nan's with None for assertion compares
        return map(lambda val: None if math.isnan(val) else val, list_vals)
    
    assert nar(output[False]['input'][0]) == nar([0, 22, 40, 47, 49, 78, 84, 125, 188, 380])
    assert nar(output[False]['input'][1]) ==  nar([68.0, 92.0, 94.0, 92.0, 104.0, 78.0, 68.0, 22.0, 14.0, 42.0])

    assert nar(output[False]['track'][0]) ==  nar([0, 22, 40, 47, 49, 78, 84, 125, 188, 380])
    assert nar(output[False]['track'][1]) == nar([54.0, 99.0, 98.0, nan, nan, 41.0, 48.0, 21.0, 8.0, 43.0])


def test_EvalDataset_buildDataset():
    
    path_test = '''data/test/evalhelpers/EvalDataset/'''
    path_gs = os.path.join('..', path_test, 'input_gs.db')
    path_answer = os.path.join('..', path_test, 'answer_outcome.pickle')

    #load listGS
    db = DBInterface(path_gs)
    listGS = [pickle.loads(d[1]) for d in db.selectAll()]
    print [_gs.frameCounter for _gs in listGS]

    # init tracker
    my_tracker = TrackFactory(on=True)
    my_tracker.setInit(ballColor = "orange")
    my_tracker.setAlgoEnum(0)

    # apply method
    evd = EvalDataset()
    evd.buildDataset(listGS, my_tracker)
    output = evd.df.copy()

    # validate
    answer = pd.read_pickle(path_answer)
    d_output, d_answer = output.to_dict(), answer.to_dict()

    assert cmp(d_output, d_answer) == 0

def test_EvalDataset_buildDataset_2():
    
    # unlike previous test, this listGS has some non-inputframes gs's.

    path_test = '''data/test/evalhelpers/EvalDataset_2/'''
    path_gs = os.path.join('..', path_test, 'input_gs.db')
    path_answer = os.path.join('..', path_test, 'answer_outcome.pickle')

    #load listGS
    db = DBInterface(path_gs)
    listGS = [pickle.loads(d[1]) for d in db.selectAll()]
    print [_gs.frameCounter for _gs in listGS]

    # init tracker
    my_tracker = TrackFactory(on=True)
    my_tracker.setInit(ballColor = "orange")
    my_tracker.setAlgoEnum(0)

    # apply method
    evd = EvalDataset()
    evd.buildDataset(listGS, my_tracker)
    output = evd.df.copy()

    answer = pd.read_pickle(path_answer)
    
    # validate
    try:
        assert output.equals(answer)
    except:
        print diff_pd(output, answer)
        raise Exception

    
def test_DFHelper_1():

    path_test = 'data/test/evalhelpers/DFHelper1/'
    path_db = os.path.join(path_test, 'eval_tmp.db')
    # path_answer = os.path.join('..', path_test, 'answer.pickle')

    #first load an outcomeData from sql
    od = OutcomeData(dbPathFn = path_db, bLoad=True, bEval=True)

    # build DFHelper objs
    df_outcome = DFHelper(od.outcomeData)
    df_eval = DFHelper(od.evalData)

    # validate inferred types
    assert df_outcome.df_type == 'outcome'
    assert df_eval.df_type == 'eval'

    # validate rowsRequested 
    df_outcome.setRowsRequested(s_cmd='inputframes')
    df_eval.setRowsRequested(s_cmd='inputframes')
    ANSWER = [0, 9, 78, 116, 136, 176, 187, 194, 195, 201, 215, 246, 270, 292, 295, 307, 308, 324, 340]
    assert [i for i,v in enumerate(df_outcome.rows_requested) if v] == ANSWER
    assert [i for i,v in enumerate(df_eval.rows_requested) if v] == ANSWER

    # validate col naming conversion
    outcome_cols = df_outcome.displayEvalMethodNames(df_outcome.df.columns).values()
    eval_cols =  df_outcome.displayEvalMethodNames(df_eval.df.columns).values()
    outcome_ANSWER = ['track\n_data0\n_0\n', 'index\n', 'track\n_data0\n_2\n', 'track\n_data0\n_3\n', 'input\n_data2\n_3\n', 'track\n_data1\n_1\n', 'track\n_data1\n_0\n', 'track\n_data1\n_3\n', 'track\n_data1\n_2\n', 'track\n_data2\n_2\n', 'track\n_data2\n_3\n', 'track\n_data2\n_0\n', 'track\n_data2\n_1\n', 'input\n_data3\n_2\n', 'track\n_data3\n_3\n', 'track\n_data3\n_2\n', 'track\n_data3\n_1\n', 'input\n_obj\n_type\n_1\n', 'track\n_obj\n_exists\n_1\n', 'track\n_obj\n_exists\n_0\n', 'track\n_obj\n_exists\n_3\n', 'track\n_obj\n_exists\n_2\n', 'input\n_obj\n_type\n_2\n', 'input\n_data2\n_1\n', 'track\n_data0\n_1\n', 'track\n_obj\n_type\n_3\n', 'track\n_obj\n_type\n_0\n', 'track\n_obj\n_type\n_1\n', 'input\n_obj\n_type\n_3\n', 'track\n_data3\n_0\n', 'input\n_data1\n_0\n', 'input\n_data1\n_1\n', 'input\n_data1\n_2\n', 'input\n_data1\n_3\n', 'track\n_obj\n_type\n_2\n', 'input\n_data0\n_1\n', 'input\n_data0\n_0\n', 'input\n_data0\n_3\n', 'input\n_data0\n_2\n', 'input\n_data2\n_2\n', 'input\n_obj\n_type\n_0\n', 'input\n_data3\n_3\n', 'input\n_data3\n_0\n', 'input\n_data3\n_1\n', 'input\n_data2\n_0\n', 'input\n_obj\n_exists\n_2\n', 'input\n_obj\n_exists\n_3\n', 'input\n_obj\n_exists\n_0\n', 'input\n_obj\n_exists\n_1\n']
    eval_ANSWER = ['check\nBaseline\nInside\nTrack\n', 'prop\nBaseline\nRadius\n', 'check\nTrack\nSuccess\n', 'check\nTrack\nInside\nBaseline\n', 'check\nEither\nContains\nOther\n', 'distance\nFrom\nBaseline\n', 'check\nBoth\nContains\nOther\n', 'compare\nRadii\n', 'prop\nTrack\nRadius\n', 'check\nTrack\nInside\nBaseline\nRect\n', 'calc\nBaseline\nBall\nUnits\nAway\n']
    assert listContainSameElems(outcome_cols, outcome_ANSWER)
    assert listContainSameElems(eval_cols, eval_ANSWER)

    # can't do that right now b/c it returns a view/not the df itself
    # properties to test: .shape / .columns / against a loaded answer
    outcome_display_df = df_outcome.getDatasetDisplay()
    eval_display_df = df_eval.getDatasetDisplay()
    assert 'input\n_data0\n_0\n' in outcome_display_df.columns
    assert outcome_display_df.shape == (19,49)
    assert 'distance\nFrom\nBaseline\n' in eval_display_df.columns
    assert eval_display_df.shape == (19,11)
    assert str.strip(eval_display_df['distance\nFrom\nBaseline\n'][0]) == '-2'
    



if __name__ == "__main__":
    # test_OutcomeData_buildScoreSchemaList()
    test_DFHelper_1()
    pass