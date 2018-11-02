import os, sys, copy, json
import subprocess
import time
import cv2
if False: from cv2 import *


from controldisplay_staging import StagingDisplay
from utils import ImgDiff

sys.path.append("../")
from modules.ControlDisplay import Display
from modules.DataSchemas import ScoreSchema


'''

TESTS:
    [ ] show_scoring_on_off_1
    [ ] show_scoring_on_off_2
        [ ] diff stub_frame size: 1280
        [ ] scoring_display check
    [ ] show_tracking_on_off_1
    
    [ ] test score_display exists
    [ ] test score_display shows appropriate annotations
    [ ] test scoring_enum=2 affects this
    [ ] diff frame size

TEST FEATURES:
    [ ] stub_frame smaller than 640
    [ ] annotateObjEnums

'''


TEST_PARENT_DIR = "../data/test/guiview/displayclass/"


def test_show_scoring_on_off_1():
    ''' test that turning show_scoring on/off affects main display panel
        test that show_scoring=on + no scoring data is handled
            
            details: different data will be different sizes
    '''


    #TODO - this goes in argument
    TEST_CHILD_DIR = "test_show_scoring_on_off_1"
    
    stub_frame          = cv2.imread(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR,
                                                    "stubframe.png"))
    bench_yes_scoring   = cv2.imread(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR,
                                                    "bench_yes_score.png"))
    bench_no_scoring    = cv2.imread(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR,
                                                    "bench_no_score.png"))

    some_scoring = ScoreSchema()
    some_scoring.addCircle([202, 162, 48, 43])    
    stub_some_score = some_scoring.getAll()

    none_scoring = ScoreSchema()
    stub_none_score = some_scoring.getAll()

    diff = ImgDiff()    #TODO - pass in log output, pass in b_log, etc.
    
    stage = StagingDisplay()
    stage.all_display_methods( b_showscoring=True 
                              ,stub_frame=stub_frame
                              ,stub_scorecurrent=stub_some_score
                              )
    scoring_on_output = stage.mock_get_frame()

    stage = StagingDisplay()
    stage.all_display_methods( b_showscoring=False                  #test-variable
                              ,stub_frame=stub_frame
                              ,stub_scorecurrent=stub_some_score
                              )
    scoring_off_output = stage.mock_get_frame()

    stage = StagingDisplay()
    stage.all_display_methods( b_showscoring=True 
                              ,stub_frame=stub_frame
                              ,stub_scorecurrent=stub_none_score    #test-variable
                              )   
    scoring_none_output = stage.mock_get_frame()
    
    #TODO - diff_imgs() -> diffImgs(), the wrapper
    
    assert diff.diffImgs(bench_yes_scoring, scoring_on_output)

    assert diff.diff_imgs(bench_no_scoring, scoring_off_output)

    assert diff.diff_imgs(bench_no_scoring, scoring_none_output)

    assert not(diff.diff_imgs(scoring_on_output, scoring_off_output))

#TODO - make the test methods
# def test_show_scoring_on_off_1():
#     test_show_scoring_on_off_1(DATA_DIR=1)
# def test_show_scoring_on_off_2():
#     test_show_scoring_on_off_1(DATA_DIR=2)


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
    test_show_scoring_on_off_1()