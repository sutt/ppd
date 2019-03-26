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

def test_CmpAlgoReport_largestDiscrepancy_2():
    ''' use custom metrics that call .distanceBetweenTracks() method'''
    
    test_path = '../data/test/evalsuite/largestDiscrepancy/'
    input_benchmark = pd.read_pickle(test_path + 'outcome_0.pickle')
    input_current = pd.read_pickle(test_path + 'outcome_2.pickle')

    cmpA = CmpAlgoReport(b_testing=True)
    cmpA.loadBenchmark(input_benchmark) 
    cmpA.loadCurrent(input_current) 

    dbt_improvement = cmpA.largestDiscrepancy(distanceBetweenTracks=1)
    
    bubt_improvement = cmpA.largestDiscrepancy(ballUnitsBetweenTracks=1)

    ANSWER = [-304.6850833237492, -283.0194339616981, -20.615528128088304, -11.661903789690601, -10.295630140987, -9.433981132056603, -8.06225774829855, -6.324555320336759, -6.082762530298219, -5.385164807134504, -5.385164807134504, -5.0990195135927845, -5.0990195135927845, -5.0, -5.0, -5.0, -4.47213595499958, -4.47213595499958, -4.47213595499958, -4.242640687119285]
    assert list(dbt_improvement) == ANSWER
    assert list(dbt_improvement.index) == [244, 202, 206, 305, 306, 163, 303, 334, 34, 336, 33, 335, 330, 210, 81, 329, 219, 49, 295, 67]

    ANSWER = [-113.20777358467925, -60.93701666474984, -4.581228472908512, -1.4907119849998598, -1.4577379737113252, -1.4285714285714286, -1.286953767623375, -1.048220125784067, -0.7010658911563956, -0.4807401700618652, -0.47140452079103173, -0.47140452079103173, -0.42591770999996, -0.4040610178208843, -0.39528470752104744, -0.375, -0.37267799624996495, -0.36363636363636365, -0.3535533905932738, -0.3516565181788127]
    assert list(bubt_improvement) == ANSWER
    print [int(x) for x in list(bubt_improvement.index)]
    assert list(bubt_improvement.index) == [202, 244, 206, 219, 305, 210, 306, 163, 303, 192, 199, 215, 295, 191, 304, 212, 200, 251, 220, 335]

    # make sure plot method is callable
    try:
        cmpA.plotTrackDistance()
    except:
        assert False


if __name__ == "__main__":
    test_CmpAlgoReport_largestDiscrepancy_1()

    


