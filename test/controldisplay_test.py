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
    [ ] zoomFrame with scoring + tracking

TEST FEATURES:
    [ ] stub_frame smaller than 640
    [x] annotateObjEnums

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
        if verifyAction(prefix = "\nrebench:" + input_test_child_dir):
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
            [x] modulo zero resize
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
        
        if verifyAction(prefix = "\nrebench:" + input_test_child_dir):
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

def test_show_tracking_on_off_2():
    
    show_tracking_on_off_1(  input_test_child_dir= "test_show_tracking_on_off_2", 
                            input_circle_data = [668, 489, 14, 14])
                            

def scoring_obj_enum(input_test_child_dir, input_obj_enum, b_wrong=False, b_rebench=False):
    ''' test that showscoring with properly formed is drawn to main_display and
        score_display
            
            input params:  - different scores (stored as json file in test dir)
                           - different scoringenum's to focus on with score_display
                           - b_wrong: if True, then there is no score with that
                                       input_obj_enum, thus no score_display
    '''

    # setup ------
    TEST_CHILD_DIR = input_test_child_dir
    
    stub_frame          = cv2.imread(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR,
                                                    "stubframe.png"))
    bench_main         = cv2.imread(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR,
                                                    "bench_main.png"))
    bench_score         = cv2.imread(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR,
                                                    "bench_score.png"))
    bench_naframe       = cv2.imread(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR,
                                                    "naframe.png"))

    stub_score_obj = ScoreSchema()

    with open(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR, "stubscore.json"), "r") as f:
        stub_score_obj.load(json.load(f))
    
    stub_score = stub_score_obj.getAll()
    
    diff = ImgDiff(log_path = DIFF_LOG_DIR)
    
    # run test -----
    
    stage = StagingDisplay()
    stage.all_display_methods( stub_frame=stub_frame.copy()
                              ,stub_scorecurrent=copy.deepcopy(stub_score)
                              ,b_showscoring = True
                              ,i_scoringenum=input_obj_enum         #test-variable
                              )
    main1 = stage.mock_get_frame()
    score1 = stage.mock_get_score_frame()

    #rebench ---
    if b_rebench:
        
        if verifyAction(prefix = "\nrebench:" + input_test_child_dir):
            return

        cv2.imwrite(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR
                                ,"bench_main.png"), main1)
        
        if b_wrong:
            
            cv2.imwrite(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR
                                    ,"naframe.png"), score1)
        else:

            cv2.imwrite(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR
                                    ,"bench_score.png"), score1)
        return
        

    # verify ----

    assert diff.diffImgs(bench_main, main1)
    
    if b_wrong:
        assert diff.diffImgs(bench_naframe, score1)
    else:
        assert diff.diffImgs(bench_score, score1)


def test_scoring_obj_enum_1():
    scoring_obj_enum("test_scoring_obj_enum_1", 0)

def test_scoring_obj_enum_2():
    scoring_obj_enum("test_scoring_obj_enum_2", 1)

def test_scoring_obj_enum_3():
    scoring_obj_enum("test_scoring_obj_enum_3", 2)

def test_scoring_obj_enum_4():
    scoring_obj_enum("test_scoring_obj_enum_4", 3)

def test_scoring_obj_enum_5():
    scoring_obj_enum("test_scoring_obj_enum_5", 2)

def test_scoring_obj_enum_6():
    scoring_obj_enum("test_scoring_obj_enum_6", 0, b_wrong=True)


def scoring_annotate_obj(input_test_child_dir, b_rebench=False):
    ''' test that we annotate score objects in main_display

            note: we can't initialize with annotateObjEnum=True or we get unhandled err
            
            input params:  - different scores (stored as json file in test dir)
    '''

    # setup ------
    TEST_CHILD_DIR = input_test_child_dir
    
    stub_frame          = cv2.imread(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR,
                                                    "stubframe.png"))
    bench_main         = cv2.imread(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR,
                                                    "bench_main.png"))
    bench_score         = cv2.imread(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR,
                                                    "bench_score.png"))
    bench_naframe       = cv2.imread(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR,
                                                    "naframe.png"))

    stub_score_obj = ScoreSchema()

    with open(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR, "stubscore.json"), "r") as f:
        stub_score_obj.load(json.load(f))
    
    stub_score = stub_score_obj.getAll()
    
    diff = ImgDiff(log_path = DIFF_LOG_DIR)
    
    # run test -----
    
    stage = StagingDisplay()
    stage.some_display_methods( p_all = True
                              ,stub_frame=stub_frame.copy()
                              ,stub_scorecurrent=copy.deepcopy(stub_score)
                              ,b_showscoring = True   
                              ,annotateObjEnum = False   #note
                              )
    stage.some_display_methods( p_all_byframe = True
                               ,p_input = True
                              ,stub_frame=stub_frame.copy()
                              ,stub_scorecurrent=copy.deepcopy(stub_score)
                              ,b_showscoring = True
                              ,annotateObjEnum = True
                              )
    main1 = stage.mock_get_frame()
    score1 = stage.mock_get_score_frame()

    #rebench ---
    if b_rebench:
        
        if verifyAction(prefix = "\nrebench:" + input_test_child_dir):
            return

        cv2.imwrite(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR
                                ,"bench_main.png"), main1)
        
        cv2.imwrite(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR
                                    ,"bench_score.png"), score1)
        return
        

    # verify ----

    assert diff.diffImgs(bench_main, main1)
    assert diff.diffImgs(bench_score, score1)

    
def test_scoring_annotate_obj_1():
    scoring_annotate_obj("test_scoring_annotate_obj_1")


def select_zoom_1(input_test_child_dir, input_zoom_roi, b_rebench=False):
    ''' test selecting an roi region and how it displays

            note: we can't fully test user input, we're only assuming that is handled
                  properly in display.show()
            
            input params:  - different scores (stored as json file in test dir)
    '''

    # setup ------
    TEST_CHILD_DIR = input_test_child_dir
    
    stub_frame          = cv2.imread(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR,
                                                    "stubframe.png"))
    bench_main         = cv2.imread(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR,
                                                    "bench_main.png"))
    bench_zoom         = cv2.imread(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR,
                                                    "bench_zoom.png"))

    diff = ImgDiff(log_path = DIFF_LOG_DIR)
    
    # run test -----
    
    stage = StagingDisplay()
    stage.some_display_methods( p_all = True
                              ,stub_frame=stub_frame.copy()
                              )
    stage.stub_set_zoom_roi(input_zoom_roi)
    stage.some_display_methods( p_all_byframe = True
                               ,p_input = True
                               ,stub_frame=stub_frame.copy()
                              )
    main1 = stage.mock_get_frame()
    zoom1 = stage.mock_get_zoom_frame()

    #rebench ---
    if b_rebench:
        if verifyAction(prefix = "\nrebench:" + input_test_child_dir):
            return
        cv2.imwrite(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR
                                    ,"bench_main.png"), main1)
        cv2.imwrite(os.path.join(TEST_PARENT_DIR, TEST_CHILD_DIR
                                    ,"bench_zoom.png"), zoom1)
        return
        

    # verify ----

    assert diff.diffImgs(bench_main, main1)
    assert diff.diffImgs(bench_zoom, zoom1)

def test_select_zoom_1():
    select_zoom_1("test_select_zoom_1", (180, 140, 100, 70))

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
    
    
    
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebench",  action="store_true", default=False)
    args = vars(ap.parse_args())

    if args["rebench"]:

        # comment these on/off to control rebench activity
        # may want to copy all tests directories into a tmp folder temporarilly
        # for rollback capabilities

        #note: the args in these params need to remain aligned with the tests above
        #       or the the rebench won't pass the test

        show_scoring_on_off_1(  input_test_child_dir= "test_show_scoring_on_off_1", 
                                input_circle_data = [202, 162, 48, 43],
                                b_rebench=True)
        
        show_scoring_on_off_1(  input_test_child_dir= "test_show_scoring_on_off_2", 
                                input_circle_data = [375, 321, 153, 132],
                                b_rebench = True)
    
        show_tracking_on_off_1(  input_test_child_dir= "test_show_tracking_on_off_1", 
                                 input_circle_data = [202, 162, 48, 43],
                                 b_rebench = True)

        show_tracking_on_off_1(  input_test_child_dir= "test_show_tracking_on_off_2", 
                                 input_circle_data = [668, 489, 14, 14],
                                 b_rebench = True)

        scoring_obj_enum("test_scoring_obj_enum_1", 0, b_rebench=True)

        scoring_obj_enum("test_scoring_obj_enum_2", 1, b_rebench=True)

        scoring_obj_enum("test_scoring_obj_enum_3", 2, b_rebench=True)

        scoring_obj_enum("test_scoring_obj_enum_4", 3, b_rebench=True)

        scoring_obj_enum("test_scoring_obj_enum_5", 2, b_rebench=True)

        scoring_obj_enum("test_scoring_obj_enum_6", 0, b_wrong=True, b_rebench=True)

        scoring_annotate_obj("test_scoring_annotate_obj_1", b_rebench=True)

        select_zoom_1("test_select_zoom_1", (180, 140, 100, 70), b_rebench=True)