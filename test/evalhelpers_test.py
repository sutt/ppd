import os, sys, json
import pandas as pd
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

    

#TODO - test OutcomeData.displayDiameterPlot as graph
#TODO - test OutcomeData.displayDiameterPlot as b_ret
#TODO - test .outcomeData.columns
#TODO - test .outcomeData.shape

if __name__ == "__main__":
    # test_OutcomeData_buildScoreSchemaList()
    pass