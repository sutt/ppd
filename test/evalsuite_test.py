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

    


