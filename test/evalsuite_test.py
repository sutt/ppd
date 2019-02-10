import os, sys, json, copy, math, pickle
import pandas as pd
import numpy as np
from utils import listContainSameElems, diff_pd
sys.path.append("../")
# from modules.DataSchemas import ScoreSchema
# from modules.ControlTracking import TrackFactory
# from modules.Interproc import DBInterface, GuiviewState
# from modules.EvalHelpers import EvalTracker, EvalDataset, OutcomeData, DFHelper
from modules.EvalSuite import EvalSuite, CmpAlgoReport




def test_CmpAlgoReport_diffDf():
    '''
        test that diffDf(df1, df2) works on multiple input data types:
            int, float, bool

        TODO
        [ ] test None -> NaN
    '''

    cmpA = CmpAlgoReport()

    # Int ------------------------------------
    df1 = pd.DataFrame({'col1': [0, 1, 2]})
    df2 = pd.DataFrame({'col1': [10, 1, 0]})

    diff_df = cmpA.diffDf(benchmark_df = df1, current_df = df2)

    d_answer = {
    'diff':{'col1':[10.0, 0.0, -2.0]},
    'current':{'col1':[10, 1, 0]},
    'benchmark':{'col1':[0, 1, 2]}
    }

    dmi = {(i,j): d_answer[i][j]
    for i in d_answer.keys()
    for j in d_answer[i].keys()}

    ANSWER = pd.DataFrame.from_dict(dmi)

    ANSWER = ANSWER[diff_df.columns]

    try:
        assert diff_pd(diff_df, ANSWER) is None
    except:
        diff_pd(diff_df, ANSWER)
        raise Exception

    # Bool -----------------------------------------
    df1 = pd.DataFrame({'col1': [True, True, False, False]})
    df2 = pd.DataFrame({'col1': [True, False, True, False]})

    diff_df = cmpA.diffDf(benchmark_df = df1, current_df = df2)

    d_answer = {
    'diff':{'col1':[0.0, -1.0, 1.0, 0.0]},
    'current':{'col1':[True, False, True, False]},
    'benchmark':{'col1':[True, True, False, False]}
    }

    dmi = {(i,j): d_answer[i][j]
    for i in d_answer.keys()
    for j in d_answer[i].keys()}

    ANSWER = pd.DataFrame.from_dict(dmi)

    ANSWER = ANSWER[diff_df.columns]

    try:
        assert diff_pd(diff_df, ANSWER) is None
    except:
        diff_pd(diff_df, ANSWER)
        raise Exception

    # Float -------------------------------------------
    df1 = pd.DataFrame({'col1': [1.1, 0.001, 0.0]})
    df2 = pd.DataFrame({'col1': [-0.2, 0.0, 0.001]})

    diff_df = cmpA.diffDf(benchmark_df = df1, current_df = df2)

    d_answer = {
    'diff':{'col1':[-1.3, -0.001, 0.001]},
    'current':{'col1':[-0.2, 0.0, 0.001]},
    'benchmark':{'col1':[1.1, 0.001, 0.0]}
    }

    dmi = {(i,j): d_answer[i][j]
    for i in d_answer.keys()
    for j in d_answer[i].keys()}

    ANSWER = pd.DataFrame.from_dict(dmi)

    ANSWER = ANSWER[diff_df.columns]

    try:
        assert diff_pd(diff_df, ANSWER) is None
    except:
        diff_pd(diff_df, ANSWER)
        raise Exception

    
def test_CmpAlgoReport_largestDiscrepancy_1():
    '''
        build your own eval table, apply the function in several ways
    '''

    # load input data
    test_path = '../data/test/evalsuite/largestDiscrepancy/'
    input_benchmark = pd.read_pickle(test_path + 'outcome_0.pickle')
    input_current = pd.read_pickle(test_path + 'outcome_2.pickle')

    cmpA = CmpAlgoReport()
    cmpA.loadBenchmark(input_benchmark) 
    cmpA.loadCurrent(input_current) 

    cts_improvement = cmpA.largestDiscrepancy(checkTrackSuccess=1)
    cts_deprovement = cmpA.largestDiscrepancy(checkTrackSuccess=-1)
    cts_absvalue = cmpA.largestDiscrepancy(checkTrackSuccess=0)

    cbco_improvement = cmpA.largestDiscrepancy(checkBothContainsOther=1, max_n=30)
    cbco_deprovement = cmpA.largestDiscrepancy(checkBothContainsOther=-1, max_n=30)
    cbco_absvalue = cmpA.largestDiscrepancy(checkBothContainsOther=0, max_n=30)

    assert [int(x) for x in cbco_improvement.index][:4] == [215, 324, 195, 0 ]
    assert [int(x) for x in cbco_deprovement.index][:4] == [0, 308, 307, 295]
    assert [int(x) for x in cbco_improvement.index][:4] == [215, 324, 195, 0 ]

    d_answer = {
    'diff':{'checkBothContainsOther':[1.0, 1.0, 1.0, 0.0] },
    'current':{'checkBothContainsOther':[True, True, True, True] },
    'benchmark':{'checkBothContainsOther':[False, False, False, True] }
    }

    dmi = {(i,j): d_answer[i][j]
    for i in d_answer.keys()
    for j in d_answer[i].keys()}

    ANSWER = pd.DataFrame.from_dict(dmi)
    ANSWER = ANSWER[['diff', 'current', 'benchmark']]

    assert (cbco_improvement[:4].values == ANSWER.values).all()
    assert (cbco_improvement.columns == ANSWER.columns).all()


if __name__ == "__main__":
    test_CmpAlgoReport_largestDiscrepancy_1()

    


