import os, sys, copy, json
import subprocess
import time
if False: from cv2 import *
from cv2 import imread

from utils import ImgDiff

sys.path.append("../")
from modules.ControlDisplay import Display
from modules.DataSchemas import ScoreSchema



'''
DEV-MODULE:

    [ ] pass in args via pytest, turn diff logging on/off
    [ ] debug indv test under __main__ with diff params

    [ ] do IF-block's in all_display_methods

    [x] test_ -> tmethod(data_dir) 
            + test_1 calls tmethod(data_dir_1) 
            + test_2 calls tmethod(data_dir_2)

'''

class StagingDisplay:

    def __init__(self):
        self.data = None

    def all_display_methods(
         self
        ,b_show         = False
        ,b_scoreoff     = False
        ,b_resize       = True
        ,b_annotate_fn  = False
        ,b_showscoring  = False
        ,i_scoringenum  = 0
        ,switchZoom     = False
        ,switchRoiMain  = False
        ,switchRoiZoom  = False
        ,switchSelectReset = False
        ,trackObjEnum   = False 
        ,trackTypeEnum  = False
        ,windowTwo      = False
        ,windowThree    = False
        ,annotateObjEnum = False
        ,cmdSelectReset = False
        ,stub_orientation = 0           # notesFactory.getOrientation()
        ,stub_vidFn     = ""            # directoryFactory.vidFn()
        ,stub_needscore = False         # outputFactory.needScore()
        ,stub_trackscore = None         # trackFactory.getTrackScore()
        ,stub_callreset = False         # trackFactory.getTrackOnChange()
        ,stub_scorecurrent = None       # notesFactory.getFrameScoreCurrent()
        ,stub_frame     = None          # frameFactory.getFrame()
        ,stub_globalsOn  = False        # func will not get/set "g.X" globals
        ):

        #init
        display = Display()
        
        display.setInit(showOn=b_show
                    ,scoreOff=b_scoreoff
                    ,frameResize=b_resize
                    ,frameAnnotateFn=b_annotate_fn)

        #byVid
        display.setOrientation(stub_orientation)
        display.setShowScoring(b_showscoring)
        display.setScoreDisplayObjEnum(i_scoringenum)
        display.reset()

        #byFrame
        display.setCmd( cmdSelectZoom=switchZoom
                        ,cmdSelectRoiMain=switchRoiMain
                        ,cmdSelectRoiZoom=switchRoiZoom
                        ,trackObjEnum=trackObjEnum
                        ,trackTypeEnum=trackTypeEnum
                        ,windowTwo=windowTwo
                        ,windowThree=windowThree
                        ,annotateObjEnum=annotateObjEnum
                        ,cmdSelectReset=switchSelectReset
                        ,globalsOn=stub_globalsOn)

        #output
        display.getScoring(stub_needscore)

        #track
        display.setTrack(trackScore = stub_trackscore)

        if stub_callreset:
            display.resetOperators()

        #ret
        display.setFrame(stub_frame)
        display.setAnnotateMsg(stub_vidFn)
        display.setScoring(stub_scorecurrent)

        display.alterFrame()
        display.drawOperators()
        display.drawTrackers()

        display.adjustOrient()
            
        display.show()

        self.data = display

    def some_display_methods(
         self
        ,p_input        = False
        ,p_all          = False
        ,p_all_byframe  = False
        ,p_init         = False
        ,p_byvid        = False
        ,p_byframe      = False
        ,p_output       = False
        ,p_track        = False
        ,p_ret          = False
        ,b_show         = False
        ,b_scoreoff     = False
        ,b_resize       = True
        ,b_annotate_fn  = False
        ,b_showscoring  = False
        ,i_scoringenum  = 0
        ,switchZoom     = False
        ,switchRoiMain  = False
        ,switchRoiZoom  = False
        ,switchSelectReset = False
        ,trackObjEnum   = False 
        ,trackTypeEnum  = False
        ,windowTwo      = False
        ,windowThree    = False
        ,annotateObjEnum = False
        ,cmdSelectReset = False
        ,stub_orientation = 0           # notesFactory.getOrientation()
        ,stub_vidFn     = ""            # directoryFactory.vidFn()
        ,stub_needscore = False         # outputFactory.needScore()
        ,stub_trackscore = None         # trackFactory.getTrackScore()
        ,stub_callreset = False         # trackFactory.getTrackOnChange()
        ,stub_scorecurrent = None       # notesFactory.getFrameScoreCurrent()
        ,stub_frame     = None          # frameFactory.getFrame()
        ,stub_globalsOn  = False        # func will not get/set "g.X" globals
        ):

        if p_input:
            display = self.data

        if p_all:
            p_init         = True
            p_byvid        = True
            p_byframe      = True
            p_output       = True
            p_track        = True
            p_ret          = True

        if p_all_byframe:
            p_byframe      = True
            p_output       = True
            p_track        = True
            p_ret          = True



        if p_init:
            display = Display()
            
            display.setInit(showOn=b_show
                        ,scoreOff=b_scoreoff
                        ,frameResize=b_resize
                        ,frameAnnotateFn=b_annotate_fn)

        if p_byvid:
            display.setOrientation(stub_orientation)
            display.setShowScoring(b_showscoring)
            display.setScoreDisplayObjEnum(i_scoringenum)
            display.reset()

        if p_byframe:
            display.setCmd( cmdSelectZoom=switchZoom
                            ,cmdSelectRoiMain=switchRoiMain
                            ,cmdSelectRoiZoom=switchRoiZoom
                            ,trackObjEnum=trackObjEnum
                            ,trackTypeEnum=trackTypeEnum
                            ,windowTwo=windowTwo
                            ,windowThree=windowThree
                            ,annotateObjEnum=annotateObjEnum
                            ,cmdSelectReset=switchSelectReset
                            ,globalsOn=stub_globalsOn)

        if p_output:
            display.getScoring(stub_needscore)

        if p_track:
            display.setTrack(trackScore = stub_trackscore)

        if stub_callreset:
            display.resetOperators()

        if p_ret:
            display.setFrame(stub_frame)
            display.setAnnotateMsg(stub_vidFn)
            display.setScoring(stub_scorecurrent)

            display.alterFrame()
            display.drawOperators()
            display.drawTrackers()

            display.adjustOrient()
                
            display.show()

        self.data = display


    def mock_get_frame(self):
        assert self.data.__class__.__name__ == "Display"
        try:
            return self.data.frame.copy()
        except:
            return None

    def mock_get_score_frame(self):
        assert self.data.__class__.__name__ == "Display"
        try:
            return self.data.scoreFrame.copy()
        except:
            return None
        