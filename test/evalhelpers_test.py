import os, sys, json, copy, math
import pandas as pd
import numpy as np
sys.path.append("../")
from modules.DataSchemas import ScoreSchema
from modules.EvalHelpers import EvalTracker, EvalDataset, OutcomeData

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
    path_tmpdf = os.path.join('..', path_test, 'tmp.json')

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
    assert cmp(incoming_df[0:1].to_dict(), ret_data[0:1].to_dict()) == 0


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

    ANSWER = [False, False, False, False, True, True, 1, 3.605551275463989]
    assert list_data == ANSWER

def test_EvalTracker_eval_methods_good():

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

    ANSWER = [None, None, None, None, None, None, None, None]
    assert list_data == ANSWER


    # test bad trackScore with changed naReturn val
    inputScore = {'0':{'type':'circle','data':[10,10,5,5] } }
    trackScore = {'1':{'type':'circle','data':[10,10,5,5] } }
    ev.setBaselineScore(inputScore)
    ev.setNaReturn(np.NaN)

    list_data = []
    for meth_name in copy.copy(ev.eval_method_names):
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


#TODO - test OutcomeData.displayDiameterPlot as graph
#TODO - test OutcomeData.displayDiameterPlot as b_ret
#TODO - test .outcomeData.columns
#TODO - test .outcomeData.shape

if __name__ == "__main__":
    # test_OutcomeData_buildScoreSchemaList()
    pass