import os, sys, copy, json
import subprocess
import time
import cv2
import pickle
if False: from cv2 import *

sys.path.append("../")
from modules.AnalysisHelpers import ( multiPlot
                                     ,applyTracker
                                     ,roiSelectZoomWindow
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
    
    test_data = "applyTracker_1.db"
    testDB = DBInterface(os.path.join(TEST_PARENT_DIR, test_data))

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
    assert data['listTransformTitles'] == ['img_t', 'img_mask', 'img_mask_2']
    assert data['listFrameTitles'] == ['0','189', '312']
    assert len(data['listScore']) == 3
    assert data['listScore'][0]['0']['data'] == (209, 168, 35, 35)
    assert data['listScore'][1] == None



def test_applyTracker_2():
    ''' test applyTracker; roiSelectFunc=None '''
    
    #load data
    tracker = TrackFactory(on=True)
    tracker.setAlgoEnum(0)
    tracker.setInit(ballColor="green")
    
    test_data = "applyTracker_1.db"
    testDB = DBInterface(os.path.join(TEST_PARENT_DIR, test_data))

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
    assert data['listTransformTitles'] == ['img_t', 'img_mask', 'img_mask_2']
    assert data['listFrameTitles'] == ['0','189', '312']
    assert len(data['listScore']) == 3
    assert data['listScore'][0]['0']['data'] == (209, 168, 35, 35)
    assert data['listScore'][1] == None


def test_applyTracker_2():
    ''' test applyTracker; roiSelectFunc=roiSelectZoomWindow.
        test_data has guiview states with a zoomRect '''
    
    #load data
    tracker = TrackFactory(on=True)
    tracker.setAlgoEnum(0)
    tracker.setInit(ballColor="green")
    
    test_data = "applyTracker_1.db"
    testDB = DBInterface(os.path.join(TEST_PARENT_DIR, test_data))

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
    assert data['listScore'][0]['0']['data'] == (17, 18, 35, 35)
    assert data['listScore'][1] == None



if __name__ == "__main__":

    test_applyTracker_1()