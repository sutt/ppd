import os, sys, copy, json
import subprocess
import time
import cv2
import pickle
import pandas as pd
from utils import ImgDiff
if False: from cv2 import *
from utils import diff_pd
sys.path.append("../")
from modules.AnalysisHelpers import ( multiPlot
                                     ,applyTracker
                                     ,roiSelectZoomWindow
                                     ,roiSelectScoreWindow
                                     ,subprocEval
                                     ,compareTrackers
                                     ,subprocBatchOutput
                                     )
from modules.ControlTracking import TrackFactory
from modules.Interproc import DBInterface, GuiviewState
from modules.DataSchemas import ScoreSchema


'''
TESTS:
    [ ] applyTracker (no roiSelect)
    [ ] applyTracker (with roiSelect)
    [ ] larger origFrame (1280) data
    [ ] arbitrary window crop rect

TEST FEATURES:
    [ ] data directory
        [ ] make
        [ ] commit to git
    [ ] need to redo applyTracker_1.db accounting for zoom window
    [ ] selectRecords(list of ints)
    [ ] how to test matplotlib?
         - try/except but suppress display? or cancel display quickly?
           catch except with assert False
         - don't even need try/except, the test will fail otherwise;
           just have assert True at the end to pass
         - any way to test the actual figure contents? ImgDiff?

NOTES:
    
    each test function has it's own db ( in the style of interproc: 
    state_tbl[id (int) s_state (str)] ), which it loads States from.
        
'''

TEST_PARENT_DIR = "../data/test/analysishelpers/"



def test_applyTracker_1():
    ''' test applyTracker; roiSelectFunc=None '''
    
    #load data
    tracker = TrackFactory(on=True)
    tracker.setAlgoEnum(0)
    tracker.setInit(ballColor="green")
    
    test_data = "applyTracker.db"
    test_dir = os.path.join(TEST_PARENT_DIR, 'applyTracker')
    testDB = DBInterface(os.path.join(test_dir, test_data))

    listGS = [  pickle.loads(record[1])
                for record in testDB.selectAll()
             ]
    
    #check input data validity
    assert [_gs.frameCounter for _gs in listGS] == [0,189,312]
    assert tracker.getTrackParams()['thresh_lo'] == (29,86,6)
    assert tracker.getTrackParams()['repair_iterations'] == 1

    #test function
    data = applyTracker(listGS, tracker)

    #check outcome
    assert len(data['listPlts']) == 3
    assert len(data['listPlts'][0]) == 3
    assert data['listPlts'][0][0].shape == (480,640,3)
    assert data['listPlts'][0][1].shape == (480,640)
    assert data['listTransformTitles'] == ['img_t', 'img_mask', 'img_repair']
    assert data['listFrameTitles'] == ['0','189', '312']
    assert len(data['listScore']) == 3
    assert data['listScore'][0]['0']['data'] == [209, 168, 35, 35]
    assert data['listScore'][1] == None



def test_applyTracker_2():
    ''' test applyTracker; roiSelectFunc=None '''
    
    #load data
    tracker = TrackFactory(on=True)
    tracker.setAlgoEnum(0)
    tracker.setInit(ballColor="green")
    
    test_data = "applyTracker.db"
    test_dir = os.path.join(TEST_PARENT_DIR, 'applyTracker')
    testDB = DBInterface(os.path.join(test_dir, test_data))

    listGS = [  pickle.loads(record[1])
                for record in testDB.selectAll()
             ]
    
    #check input data validity
    assert [_gs.frameCounter for _gs in listGS] == [0,189,312]
    assert tracker.getTrackParams()['thresh_lo'] == (29,86,6)
    assert tracker.getTrackParams()['repair_iterations'] == 1

    #test function
    data = applyTracker(listGS, tracker)

    #check outcome
    assert len(data['listPlts']) == 3
    assert len(data['listPlts'][0]) == 3
    assert data['listPlts'][0][0].shape == (480,640,3)
    assert data['listPlts'][0][1].shape == (480,640)
    assert data['listTransformTitles'] == ['img_t', 'img_mask', 'img_repair']
    assert data['listFrameTitles'] == ['0','189', '312']
    assert len(data['listScore']) == 3
    assert data['listScore'][0]['0']['data'] == [209, 168, 35, 35]
    assert data['listScore'][1] == None


def test_applyTracker_3():
    ''' test applyTracker; roiSelectFunc=roiSelectZoomWindow.
        test_data has guiview states with a zoomRect '''
    
    #load data
    tracker = TrackFactory(on=True)
    tracker.setAlgoEnum(0)
    tracker.setInit(ballColor="green")
    
    test_data = "applyTracker.db"
    test_dir = os.path.join(TEST_PARENT_DIR, 'applyTracker')
    testDB = DBInterface(os.path.join(test_dir, test_data))

    listGS = [  pickle.loads(record[1])
                for record in testDB.selectAll()
             ]
    
    #check input data validity
    assert [_gs.frameCounter for _gs in listGS] == [0,189,312]

    #test function
    data = applyTracker(listGS, tracker, roiSelectZoomWindow)

    #check outcome
    assert data['listPlts'][0][0].shape == (68,66,3)
    assert data['listPlts'][0][1].shape == (68,66)
    assert data['listPlts'][1][0].shape == (22,22,3)
    assert data['listPlts'][1][1].shape == (22,22)
    
    assert len(data['listScore']) == 3
    assert data['listScore'][0]['0']['data'] == [17, 18, 35, 35]
    assert data['listScore'][1] == None

def test_subprocEval_1():
    
    path_test = 'data/test/analysishelpers/subprocEval/'

    vid_path = os.path.join(path_test, 'ss1.avi')
    db_path = os.path.join(path_test, 'test_eval_db.db')
    
    answer_path = os.path.join('..', path_test, 'answer.pickle')

    output = subprocEval(f_pathfn=vid_path, db_pathfn=db_path)

    answer = pd.read_pickle(answer_path)

    try:
        assert output.equals(answer)
    except:
        diff_pd(answer, output)
        raise Exception

def test_compareTrackers_1():
    '''
        functionality test for:
             basic functionality
             roiSelectWindow
             bMarkedFrame
             success calling multiPlot
             multiplot_params
    '''
    
    # build listTrackers
    listTrackers = []
    for _algoenum in [0,1]:
        _tracker = TrackFactory(on=True)
        _tracker.setAlgoEnum(_algoenum)
        _tracker.setInit(ballColor="orange")
        listTrackers.append(_tracker)
    
    # build listGS
    test_data = "compareTrackers_orange.db"
    test_dir = os.path.join(TEST_PARENT_DIR, 'compareTrackers')
    testDB = DBInterface(os.path.join(test_dir, test_data))
    listGS = [  pickle.loads(record[1])
                for record in testDB.selectAll()]

    # run method with test_mock flag
    data_dict = compareTrackers(listGS, listTrackers, test_stub=True)

    # checks
    print data_dict['row_titles']
    assert data_dict['row_titles'] == ['marked_frame', 'img_t', 'img_mask', 'img_repair', 'img_terminal']
    assert data_dict['col_titles'] == ['AlgoEnum=0', 'AlgoEnum=1']
    assert data_dict['plot_data'][0][1].shape == (480,640,3)  # since roiSelectFunc=None

    # run 1. without markedFrame at the top, 2. with selectRoiFunc
    data_dict = compareTrackers(listGS, listTrackers
                                ,roiSelectFunc=True
                                ,bMarkedFrame=False
                                ,test_stub=True)

    assert data_dict['row_titles'] == ['img_t', 'img_mask', 'img_repair', 'img_terminal']
    assert data_dict['plot_data'][0][1].shape != (480,640, 3)

    # don't run with test_stub; thus sending data into multiPlot() to see 
    # if any exceptions are thrown. use bSupressDisplay to prevent matplotlib output
    # from popping-up during the tests
    compareTrackers(listGS, listTrackers
                    ,test_stub=False
                    ,multiplot_params = {'figsize': (20,20), 'bSupressDisplay': True}
                    )


def test_compareTrackers_2():
    '''
        test functionality:
            col_titles
            expand_factor
            blend_rowtitles
            pixel-comparison
    '''

    # build listTrackers
    listTrackers = []
    for _algoenum in [0,1]:
        _tracker = TrackFactory(on=True)
        _tracker.setAlgoEnum(_algoenum)
        _tracker.setInit(ballColor="orange")
        listTrackers.append(_tracker)
    
    # build listGS
    test_data = "compareTrackers_orange.db"
    test_dir = os.path.join(TEST_PARENT_DIR, 'compareTrackers')
    testDB = DBInterface(os.path.join(test_dir, test_data))
    listGS = [  pickle.loads(record[1])
                for record in testDB.selectAll()]

    # run two separate functions with different params, compare their output
    
    data_dict_1 = compareTrackers(listGS, listTrackers, roiSelectFunc=True
                                ,col_titles = ['my_col_1', 'my_col_2']
                                ,test_stub=True)

    data_dict_2 = compareTrackers(listGS, listTrackers, roiSelectFunc=True
                                ,expand_factor = 0.5
                                ,blend_rowtitles = True
                                ,test_stub=True)

    # checks
    assert data_dict_1['row_titles'] == ['marked_frame', 'img_t', 'img_mask', 'img_repair', 'img_terminal']
    assert data_dict_2['row_titles'] == ['marked_frame\nmarked_frame', 'img_t\nimg_t', 'img_mask\nimg_mask', 'img_repair\nimg_repair', 'n/a\nimg_terminal']
    
    assert data_dict_1['col_titles'] == ['my_col_1', 'my_col_2']
    assert data_dict_2['col_titles'] == ['AlgoEnum=0', 'AlgoEnum=1']

    assert (data_dict_1['plot_dict']['img_t'][0].shape[0] < 
            data_dict_2['plot_dict']['img_t'][0].shape[0])
    
    
    # verify plots in blend_rowtitles is in correct order
    # data_dict_2['plot_data'][col][row] is None
    # data_dict_2['plot_data'][col][row] is not None

    
    # pixel-wise comparison
    DIFF_LOG_DIR = "../data/test/guiview/displayclass/log/"
    diff = ImgDiff(log_path = DIFF_LOG_DIR)
    
    loaded_mf1 = cv2.imread(os.path.join(test_dir, 'benchmark_markedframe_1.png'))
    loaded_mf2 = cv2.imread(os.path.join(test_dir, 'benchmark_markedframe_2.png'))

    mf1 = data_dict_1['plot_dict']['marked_frame'][0]
    mf2 = data_dict_2['plot_dict']['marked_frame'][0]

    assert diff.diffImgs(mf1, loaded_mf1)
    assert diff.diffImgs(mf2, loaded_mf2)

def test_compareTrackers_3():
    '''
        test functionality:
            aligning algo's with different num of diagnostic-plots
    '''

    # build listTrackers
    listTrackers = []
    for _algoenum in [2,3]:
        _tracker = TrackFactory(on=True)
        _tracker.setAlgoEnum(_algoenum)
        _tracker.setInit(ballColor="orange")
        listTrackers.append(_tracker)
    
    # build listGS
    test_data = "compareTrackers_orange.db"
    test_dir = os.path.join(TEST_PARENT_DIR, 'compareTrackers')
    testDB = DBInterface(os.path.join(test_dir, test_data))
    listGS = [  pickle.loads(record[1])
                for record in testDB.selectAll()]

    # run two separate functions with different params, compare their output
    
    data_dict_1 = compareTrackers(listGS, listTrackers, roiSelectFunc=True
                                ,test_stub=True)

    data_dict_2 = compareTrackers(listGS, listTrackers, roiSelectFunc=True
                                ,expand_factor = 0.5
                                ,blend_rowtitles = True
                                ,test_stub=True)

    # checks
    
    assert data_dict_1['row_titles'] == ['marked_frame', 'img_t', 'img_mask', 'img_repair', 'img_dummy', 'img_dummy_2', 'img_terminal', 'img_terminal_2']
    print data_dict_2['row_titles']
    assert data_dict_2['row_titles'] == ['marked_frame\nmarked_frame', 'img_t\nimg_t', 'img_mask\nimg_mask', 'img_repair\nimg_repair','img_terminal\nimg_dummy', 'n/a\nimg_dummy_2', 'n/a\nimg_terminal', 'n/a\nimg_terminal_2']

    assert sum(sum(sum(data_dict_1['plot_dict']['img_t'][0]))) > 0
    assert data_dict_1['plot_dict']['img_dummy'][0] is None
    assert sum(sum(sum(data_dict_1['plot_dict']['img_dummy'][1]))) > 0

    assert data_dict_2['plot_dict']['img_dummy'][0] is None
    assert sum(sum(sum(data_dict_2['plot_dict']['img_dummy'][1]))) > 0

    assert data_dict_1['plot_data'][0][7] is None
    # assert sum(sum(sum(data_dict_1['plot_data'][1][7]))) > 0

def test_compareTrackers_4():
    '''
        test functionality:
            bFirstTrackerRoi
    '''

    # build listTrackers: place algo_enum=2 in first position
    listTrackers = []
    for _algoenum in [2,0]:
        _tracker = TrackFactory(on=True)
        _tracker.setAlgoEnum(_algoenum)
        _tracker.setInit(ballColor="orange")
        listTrackers.append(_tracker)
    
    # build listGS - these foi's are specifically chosen as the roi from track_score
    # from algo_enum=0 and algo_enum=2 are very different
    test_data = "compareTrackers_disparateRoi.db"
    test_dir = os.path.join(TEST_PARENT_DIR, 'compareTrackers')
    testDB = DBInterface(os.path.join(test_dir, test_data))
    listGS = [  pickle.loads(record[1])
                for record in testDB.selectAll()]

    # run two separate functions with different params, compare their output
    
    data_indv_roi = compareTrackers(listGS
                                ,listTrackers
                                ,roiSelectFunc=True
                                ,bTrackScore=True
                                ,bFirstTrackerRoi=False     # var-of-interest
                                ,expand_factor=2.0
                                ,test_stub=True)

    data_first_roi = compareTrackers(listGS
                                ,listTrackers
                                ,roiSelectFunc=True
                                ,bTrackScore=True
                                ,bFirstTrackerRoi=True     # var-of-interest
                                ,expand_factor=2.0
                                ,test_stub=True)

    
    #compare col_titles - extract window-roi from string
    assert data_indv_roi['col_titles'] == ['AlgoEnum=2\n(373, 277, 10, 10)', 'AlgoEnum=0\n(395, -7, 16, 16)']
    assert data_first_roi['col_titles'] == ['AlgoEnum=2\n(373, 277, 10, 10)', 'AlgoEnum=0\n(373, 277, 10, 10)']

    #make sure empty plot is in correct position - the second position
    plot_row = data_indv_roi['plot_dict']['img_terminal']
    assert sum(sum(plot_row[0])) > 0
    assert  plot_row[1] is None
    plot_row = data_first_roi['plot_dict']['img_terminal']
    assert sum(sum(plot_row[0])) > 0
    assert  plot_row[1] is None

    # use shape to verify the same roi is being applied across all trackers
    
    assert (data_indv_roi['plot_dict']['img_t'][0].shape 
            != 
            data_indv_roi['plot_dict']['img_t'][1].shape)

    assert (data_first_roi['plot_dict']['img_t'][0].shape 
            == 
            data_first_roi['plot_dict']['img_t'][1].shape)

def test_compareTrackers_5():
    '''
        test functionality:
            blend_rowtitles
    '''

    # build listTrackers
    listTrackers = []
    for _algoenum in [2,3]:
        _tracker = TrackFactory(on=True)
        _tracker.setAlgoEnum(_algoenum)
        _tracker.setInit(ballColor="orange")
        listTrackers.append(_tracker)
    
    # build listGS
    test_data = "compareTrackers_orange.db"
    test_dir = os.path.join(TEST_PARENT_DIR, 'compareTrackers')
    testDB = DBInterface(os.path.join(test_dir, test_data))
    listGS = [  pickle.loads(record[1])
                for record in testDB.selectAll()]

    # run with blend_rowtitles

    data_dict_2 = compareTrackers(listGS, listTrackers, roiSelectFunc=True
                                ,expand_factor = 0.5
                                ,blend_rowtitles = True
                                ,test_stub=True)

    # checks
    print data_dict_2['row_titles']
    assert data_dict_2['row_titles'] == ['marked_frame\nmarked_frame', 'img_t\nimg_t', 'img_mask\nimg_mask', 'img_repair\nimg_repair', 'img_terminal\nimg_dummy', 'n/a\nimg_dummy_2','n/a\nimg_terminal','n/a\nimg_terminal_2']
    
    # verify plots in blend_rowtitles is in correct order
    data_dict_2['plot_data'][0][4] is not None
    try:
        data_dict_2['plot_data'][0][5] is None
        assert False  # this should be out-of-index
    except:
        pass
    data_dict_2['plot_data'][1][4] is not None
    data_dict_2['plot_data'][1][5] is not None


    
def test_compareTrackers_orderDict_1():
    ''' copy over the inner function to see if it works as advertised '''
    
    def updateOrderDict(order_dict, tmp_names):
        ''' if there's a new key/row_title, add it at its current position 
            and shift all higher values up one
        '''
        for _i, _name in enumerate(tmp_names):

            if _name in order_dict.keys():
                continue
            else:
                if _i == 0:
                    new_i = 0
                else:
                    new_i = order_dict[tmp_names[_i-1]] + 1
                for _item in order_dict.items():
                    k, v = _item[0], _item[1]
                    if v >= new_i:
                        order_dict[k] = v + 1
                order_dict[_name] = new_i
        return order_dict

    order_dict = {}

    tmp_names = ['genesis', 'revelations']
    order_dict = updateOrderDict(order_dict, tmp_names)

    tmp_names = ['genesis', 'gospel']
    order_dict = updateOrderDict(order_dict, tmp_names)

    tmp_names = ['genesis', 'exodus']
    order_dict = updateOrderDict(order_dict, tmp_names)

    tmp_names = ['revelations', 'self-help', 'post-help']
    order_dict = updateOrderDict(order_dict, tmp_names)

    tmp_names = ['exodus', 'gospel']
    order_dict = updateOrderDict(order_dict, tmp_names)

    elems = order_dict.items()

    # note - .items() doesn't neccesarily return in sorted order
    # so, we compare each elem separately
    assert ('genesis', 0) in elems
    assert ('exodus', 1) in elems
    assert ('gospel', 2) in elems
    assert ('revelations', 3) in elems
    assert ('self-help', 4) in elems
    assert ('post-help', 5) in elems

def debug_reveresed_plots():

    # build listGS
    foi = [202, 206, 210, 244, 305]
    vid_fn = 'data/proc/tmp/dec14/output5.proc1.proc1.avi'
    listGS = subprocBatchOutput(vid_fn, batch_list = foi)
    
    
    #build trackers
    listTrackers = []
    for _algoenum in [0,2]:
        _tracker = TrackFactory(on=True)
        _tracker.setAlgoEnum(_algoenum)
        _tracker.setInit(ballColor="orange")
        listTrackers.append(_tracker)
    print 'algo_enums=', str([_tracker.tp_trackAlgoEnum for _tracker in listTrackers])
    listTrackers.sort(reverse=True)
    print 'algo_enums=', str([_tracker.tp_trackAlgoEnum for _tracker in listTrackers])


    #run method
    ret = compareTrackers(listGS
                ,listTrackers
                ,roiSelectFunc=True
                ,bMarkedFrame=True
                ,bTrackScore=True
                ,bFirstTrackerRoi=True
                ,expand_factor=5.0
               ,test_stub=True
               )


if __name__ == "__main__":

    test_compareTrackers_5()
    # test_compareTrackers_orderDict_1()
    # test_compareTrackers_3()
    # debug_reveresed_plots()