import os, sys, copy, json
import subprocess
import time
import cv2
if False: from cv2 import *


from controldisplay_staging import StagingDisplay
from utils import ImgDiff
from utils import verifyAction

sys.path.append("../")
from modules.ControlDisplay import Display
from modules.DataSchemas import ScoreSchema


'''

TESTS:
    [x] show_scoring_on_off_1
    [x] show_scoring_on_off_2
        [x] diff stub_frame size: 1280
    
    [ ] scoring_display check
    [ ] show_tracking_on_off_1
    
    [ ] test score_display exists
    [ ] test score_display shows appropriate annotations
    [ ] test scoring_enum=2 affects this
    [ ] diff frame size

TEST FEATURES:
    [ ] stub_frame smaller than 640
    [ ] annotateObjEnums

DOCUMENTATION:

    on a test fail:
        we can examine the change two ways:
            1. numerical diffs should be printed to stdout, and returned in pytest
            2. visually with an image in data/test/guiview/displayclass/log
    
    >python controldisplay_test.py --rebench

        this allows you to take data created during test and write to test's benchmark data
        
        note: you want to rebench data-img's with bench_ prefix, but stub_frame etc
              should remain unchanged.

'''


TEST_PARENT_DIR = "../data/test/guiview/displayclass/"
DIFF_LOG_DIR = "../data/test/guiview/displayclass/log/"


def show_scoring_on_off_1(input_test_child_dir, input_circle_data, b_rebench=False):
    ''' test that turning show_scoring on/off affects main display panel
        test that show_scoring=on + no scoring data is handled
            
            input params:  - tests have dif size frames
                           - tests have dif scoring-data
    '''

    # setup ------
    TEST_CHILD_DIR = input_test_child_dir
    
    stub_frame          = cv2.imread(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR,
                                                    "stubframe.png"))
    bench_yes_scoring   = cv2.imread(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR,
                                                    "bench_yes_score.png"))
    bench_no_scoring    = cv2.imread(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR,
                                                    "bench_no_score.png"))

    some_scoring = ScoreSchema()
    some_scoring.addCircle(input_circle_data)
    stub_some_score = some_scoring.getAll()

    none_scoring = ScoreSchema()
    stub_none_score = none_scoring.getAll()

    diff = ImgDiff(log_path = DIFF_LOG_DIR)
    
    # run test -----
    stage = StagingDisplay()
    stage.all_display_methods( b_showscoring=True 
                              ,stub_frame=stub_frame.copy()
                              ,stub_scorecurrent=copy.deepcopy(stub_some_score)
                              )
    scoring_on_output = stage.mock_get_frame()

    stage = StagingDisplay()
    stage.all_display_methods( b_showscoring=False                  #test-variable
                              ,stub_frame=stub_frame.copy()
                              ,stub_scorecurrent=copy.deepcopy(stub_some_score)
                              )
    scoring_off_output = stage.mock_get_frame()

    stage = StagingDisplay()
    stage.all_display_methods( b_showscoring=True 
                              ,stub_frame=stub_frame.copy()
                              ,stub_scorecurrent=copy.deepcopy(stub_none_score)    #test-variable
                              )   
    scoring_none_output = stage.mock_get_frame()

    #rebench ---
    if b_rebench:
        if verifyAction(prefix = "rebench:" + input_test_child_dir):
            return
        cv2.imwrite(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR, "bench_yes_score.png")
                    ,scoring_on_output)
        cv2.imwrite(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR, "bench_no_score.png")
                    ,scoring_off_output)
        return
        

    # verify ----
    assert diff.diffImgs(bench_yes_scoring, scoring_on_output)

    assert diff.diffImgs(bench_no_scoring, scoring_off_output)

    assert diff.diffImgs(bench_no_scoring, scoring_none_output)

    assert diff.diffImgs(scoring_on_output, scoring_off_output, noLog=True) == False


def test_show_scoring_on_off_1():
    
    show_scoring_on_off_1(  input_test_child_dir= "test_show_scoring_on_off_1", 
                            input_circle_data = [202, 162, 48, 43])

def test_show_scoring_on_off_2():
    
    show_scoring_on_off_1(  input_test_child_dir= "test_show_scoring_on_off_2", 
                            input_circle_data = [375, 321, 153, 132])

def show_tracking_on_off_1(input_test_child_dir, input_circle_data, b_rebench=False):
    ''' test that turning tracking on/off affecta main_display
        and that it affects score_display
            
            input params:  - tests have dif size frames
                           - tests have dif scoring-data

        TODO:
            [ ] modulo zero resize
    '''

    # setup ------
    TEST_CHILD_DIR = input_test_child_dir
    
    stub_frame          = cv2.imread(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR,
                                                    "stubframe.png"))
    bench_yes_tracking   = cv2.imread(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR,
                                                    "bench_yes_track_main.png"))
    bench_no_tracking    = cv2.imread(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR,
                                                    "bench_no_track_main.png"))
    bench_score         = cv2.imread(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR,
                                                    "bench_yes_track_score.png"))

    some_scoring = ScoreSchema()
    some_scoring.addCircle(input_circle_data)
    stub_some_score = some_scoring.getAll()

    none_scoring = ScoreSchema()
    stub_none_score = none_scoring.getAll()

    diff = ImgDiff(log_path = DIFF_LOG_DIR)
    
    # run test -----
    
    #1:
    stage = StagingDisplay()
    stage.all_display_methods( stub_frame=stub_frame.copy()
                              ,stub_trackscore=copy.deepcopy(stub_some_score)
                              )
    main1 = stage.mock_get_frame()
    score1 = stage.mock_get_score_frame()
    

    #2:
    stage = StagingDisplay()
    stage.all_display_methods( stub_frame=stub_frame.copy()
                              ,stub_trackscore=copy.deepcopy(stub_none_score)   #test-variable
                              )
    main2 = stage.mock_get_frame()
    score2 = stage.mock_get_score_frame()

    #3:
    stage = StagingDisplay()
    stage.all_display_methods( b_showscoring=True                                 #test-variable
                              ,stub_frame=stub_frame.copy()
                              ,stub_trackscore=copy.deepcopy(stub_some_score)    
                              )   
    main3 = stage.mock_get_frame()
    score3 = stage.mock_get_score_frame()

    #rebench ---
    if b_rebench:
        
        if verifyAction(prefix = "rebench:" + input_test_child_dir):
            return

        cv2.imwrite(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR
                                ,"bench_yes_track_main.png"), main1)
        cv2.imwrite(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR
                                ,"bench_no_track_main.png"), main2)
        cv2.imwrite(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR
                                ,"bench_yes_track_score.png"), score3)
        return
        

    # verify ----

    assert diff.diffImgs(bench_yes_tracking, main1)

    assert diff.diffImgs(bench_no_tracking, main2)

    assert diff.diffImgs(bench_yes_tracking, main3)

    assert diff.diffImgs(main1, main2, noLog=True) == False

    assert diff.diffImgs(bench_score, score1)
    
    assert score2 is None

    assert diff.diffImgs(bench_score, score3)



def test_show_tracking_on_off_1():
    
    show_tracking_on_off_1(  input_test_child_dir= "test_show_tracking_on_off_1", 
                            input_circle_data = [202, 162, 48, 43])

# Indv. Method Tests -----------------------

def test_mindimsforrect_1():
    ''' simple min_scalar_wdith examples '''

    BOUNDS = (480, 640)

    rect = (100, 100, 100, 10)
    out = Display.minDimsForRect(
                        rect
                        ,BOUNDS
                        ,min_scalar_width=20
                        ,max_multiple_width=None
                        )
    assert out == (100,95,100,20)

    rect = (100, 100, 10, 100)
    out = Display.minDimsForRect(
                        rect
                        ,BOUNDS
                        ,min_scalar_width=20
                        ,max_multiple_width=None
                        )
    assert out == (95,100,20,100)

    rect = (100, 100, 10, 10)
    out = Display.minDimsForRect(
                        rect
                        ,BOUNDS
                        ,min_scalar_width=20
                        ,max_multiple_width=None
                        )
    assert out == (95,95,20,20)


def test_mindimsforrect_2():
    ''' min_scalar_wdith with non modulo-zero expansion '''

    BOUNDS = (480, 640)

    rect = (100, 100, 100, 5)
    out = Display.minDimsForRect(
                        rect
                        ,BOUNDS
                        ,min_scalar_width=10
                        ,max_multiple_width=None
                        )
    assert out == (100,97,100,10)


def test_mindimsforrect_3():
    ''' min_scalar_wdith examples: that collide with bounds '''
    
    BOUNDS = (480, 640)

    rect = (0, 0, 100, 10)
    out = Display.minDimsForRect(
                        rect
                        ,BOUNDS
                        ,min_scalar_width=20
                        ,max_multiple_width=None
                        )
    assert out == (0, 0, 100, 20)

    rect = (630, 100, 10, 100)
    out = Display.minDimsForRect(
                        rect
                        ,BOUNDS
                        ,min_scalar_width=20
                        ,max_multiple_width=None
                        )
    assert out == (620, 100, 20, 100)

    rect = (630, 100, 10, 100)
    out = Display.minDimsForRect(
                        rect
                        ,BOUNDS
                        ,min_scalar_width=20
                        ,max_multiple_width=None
                        )
    assert out == (620, 100, 20, 100)


def test_mindimsforrect_4():
    ''' check that max_multiple_wdith does not interfere with
         min_scalar_width 
    '''

    BOUNDS = (480, 640)

    rect = (100, 100, 100, 10)
    out = Display.minDimsForRect(
                        rect
                        ,BOUNDS
                        ,min_scalar_width=20
                        ,max_multiple_width=20
                        )
    assert out == (100,95,100,20)

    rect = (100, 100, 10, 100)
    out = Display.minDimsForRect(
                        rect
                        ,BOUNDS
                        ,min_scalar_width=20
                        ,max_multiple_width=20
                        )
    assert out == (95,100,20,100)


def test_mindimsforrect_5():
    ''' simple max_multiple_wdith '''

    BOUNDS = (480, 640)

    rect = (100, 100, 100, 10)
    out = Display.minDimsForRect(
                        rect
                        ,BOUNDS
                        ,min_scalar_width=None
                        ,max_multiple_width=5
                        )
    assert out == (100,95,100,20)

    rect = (100, 100, 10, 100)
    out = Display.minDimsForRect(
                        rect
                        ,BOUNDS
                        ,min_scalar_width=None
                        ,max_multiple_width=5
                        )
    assert out == (95,100,20,100)

def test_mindimsforrect_6():
    ''' max_multiple_width examples: that collide with bounds '''
    
    BOUNDS = (480, 640)

    rect = (0, 0, 100, 10)
    out = Display.minDimsForRect(
                        rect
                        ,BOUNDS
                        ,min_scalar_width=None
                        ,max_multiple_width=5
                        )
    assert out == (0, 0, 100, 20)

    rect = (630, 100, 10, 100)
    out = Display.minDimsForRect(
                        rect
                        ,BOUNDS
                        ,min_scalar_width=None
                        ,max_multiple_width=5
                        )
    assert out == (620, 100, 20, 100)


def test_display_rectToCircle():
    
    rect = (0,0,10,10)
    x,y,r = Display.rectToCircle(rect)

    assert x == 5
    assert y == 5 
    assert r == 5

    rect = (2,1,10,12)
    x,y,r = Display.rectToCircle(rect)

    assert x == 7
    assert y == 7 
    assert r == 5

    rect = (2,1,11,12)
    x,y,r = Display.rectToCircle(rect)

    assert x == 7
    assert y == 7 
    assert r == 5


if __name__ == "__main__":
    
    # test_show_tracking_on_off_1()
    # sys.exit()

    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebench",  action="store_true", default=False)
    args = vars(ap.parse_args())

    if args["rebench"]:

        # comment these on/off to control rebench activity
        # may want to copy all tests directories into a tmp folder temporarilly
        # for rollback capabilities

        show_scoring_on_off_1(  input_test_child_dir= "test_show_scoring_on_off_1", 
                                input_circle_data = [202, 162, 48, 43],
                                b_rebench=True)
        
        show_scoring_on_off_1(  input_test_child_dir= "test_show_scoring_on_off_2", 
                                input_circle_data = [375, 321, 153, 132],
                                b_rebench = True)
    
        show_tracking_on_off_1(  input_test_child_dir= "test_show_tracking_on_off_1", 
                                 input_circle_data = [202, 162, 48, 43],
                                 b_rebench = True)


