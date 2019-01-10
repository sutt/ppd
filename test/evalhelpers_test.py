import os, sys, json
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



#TODO - test OutcomeData.displayDiameterPlot as graph
#TODO - test OutcomeData.displayDiameterPlot as b_ret
#TODO - test .outcomeData.columns
#TODO - test .outcomeData.shape