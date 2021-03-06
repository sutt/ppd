import os, sys, time
import numpy as np
import cv2
import argparse
import modules.GlobalsC as g
from modules.myutils import (uniqueFn, parseCliList)
from modules.GuiC import (GuiC, GuiInterface)
from modules.filelog import (TimeLog, MetaDataLog)
from modules.ControlFlow import ( DirectoryFactory
                                 ,FrameFactory
                                 ,TimeFactory
                                 ,OutputFactory
                                 ,NotesFactory
                                )
from modules.ControlDisplay import Display
from modules.ControlTracking import TrackFactory
from modules.ControlEval import EvalFactory

if False: from cv2 import *  # for vscode intellisense

'''
    main script for viewing and evaluating videos
        
'''

#Globals---------------------------------
# carry info from gui -> mainthread
g.init()
g.playOn = True
g.switchAdvanceFrame = False
g.switchRetreatFrame = False
g.switchRewind = False
g.switchFastforward = False
g.frameDelay = True
g.callExit = False
g.delaySecs = 0.0
g.writevidOn = False
g.initWriteVid = False
g.switchWriteVid = False
g.switchZoom = False
g.switchRoiMain = False
g.switchRoiZoom = False
g.windowTwo = True
g.windowThree = True
g.switchWriteScoring = False
g.compressionEnum = 0
g.trackingOn = False
g.switchOutputParams = False
g.switchAlterParams = False
g.switchResetParams = False
g.duplicatesEnum = 0
g.switchOverideNote = False
g.trackObjEnum = 0
g.trackTypeEnum = 0
g.annotateObjEnum = False
g.switchSelectReset = False
g.switchOutputState = False
g.switchDeleteState = False


#High Level Options --------------------------
b_play_dir = False
b_preload = True
b_annotate_fn = False
b_resize = True
b_gui = True
first_n = 0
b_test = False
str_test = ""
b_show = True
framelog_pathfn = ""
b_showscoring = False
i_scoringenum = 0
f_scoredelay = 1.0
b_scoreoff = False
b_output_tracktimer = False
i_algo_enum = 0
b_batch_output = False
i_batch_output_enum = 0
l_batch_output_list = None
s_batch_db_pathfn = ""
s_eval_db_pathfn = ""
b_eval = False
b_eval_log = False

#CLI Flags ----------------------------------
ap = argparse.ArgumentParser()
ap.add_argument("--dir", type=str, default="")
ap.add_argument("--file", type=str, default="")
ap.add_argument("--nogui",  action="store_true", default=False)
ap.add_argument("--nodelay", action="store_true", default=False)
ap.add_argument("--preload", action="store_true", default=False)
ap.add_argument("--dontload", action="store_true", default=False)
ap.add_argument("--firstN", type=str, default="")
ap.add_argument("--test", type=str, default="")
ap.add_argument("--noshow", action="store_true", default=False)
ap.add_argument("--output", type=str, default="")
ap.add_argument("--framelog", type=str, default="")
ap.add_argument("--showscoring", action="store_true", default=False)
ap.add_argument("--scoringenum", type=str, default="")
ap.add_argument("--scoreoff", action="store_true", default=False)
ap.add_argument("--track", action="store_true", default=False)
ap.add_argument("--startplay", action="store_true", default=False)
ap.add_argument("--tracktimer", action="store_true", default=False)
ap.add_argument("--allowduplicates", action="store_true", default=False)
ap.add_argument("--algoenum", type=str, default="")
ap.add_argument("--batchoutputenum", type=str, default="")
ap.add_argument("--batchoutputlist", type=str, default="")
ap.add_argument("--batchdbpathfn", type=str, default="")
ap.add_argument("--evaldbpathfn", type=str, default="")
ap.add_argument("--eval", action="store_true", default=False)
ap.add_argument("--evallog", action="store_true", default=False)
args = vars(ap.parse_args())


#Run Type: sets options / override defaults ----

if args["file"] != "":
    
    PATH_FN = args["file"]
    PATH, FN = os.path.split(PATH_FN)
    init_dir = os.path.realpath(PATH)
    
    b_preload = True
    g.playOn = False
    
    g.switchAdvanceFrame = True
    
    
if args["dir"] != "":
    FN = ""
    init_dir = os.path.realpath(args["dir"])

    b_play_dir = True
    b_preload = False
    b_annotate_fn = True
    b_resize = True
    
    g.frameDelay = False
    # b_showscoring = True
    f_scoredelay = 0.3


if args["test"] != "":
    
    b_test = True
    str_test = args["test"]

    from test.guiview_test import GuiviewStub
    from test.guiview_test import GuiviewMock
    stub = GuiviewStub(str_test)
    mock = GuiviewMock(str_test)


if args["nogui"]:
    b_gui = False

if args["nodelay"]:
    g.frameDelay = False

if args["preload"]:
    b_preload = True

if args["firstN"] != "":
    first_n = int(args["firstN"])

if args["noshow"]:
    b_show = False

if args["framelog"]:
    framelog_pathfn = args["framelog"]
    
if args["dontload"]:
    b_preload = False

if args["showscoring"]:
    b_showscoring = True
    
if args["scoringenum"] != "":
        try: i_scoringenum = int(args["scoringenum"])
        except: pass

if args["scoreoff"]:
    # suppress zoom window from automatically popping up 
    # for showscoring or track-on cases
    b_scoreoff = True

if args["track"]:
    g.trackingOn = True

if args["startplay"]:
    # helpful for running debug with --file and --nogui
    g.playOn = True

if args["tracktimer"]:
    b_output_tracktimer = True

if args["allowduplicates"]:
    g.duplicatesEnum = 1

if args["algoenum"] != "":
    i_algo_enum = int(args["algoenum"])

if args["batchoutputenum"] != "":
    b_batch_output = True
    i_batch_output_enum = int(args["batchoutputenum"])
    
if args["batchoutputlist"] != "":
    b_batch_output = True
    i_batch_output_enum = 1
    l_batch_output_list = parseCliList( args["batchoutputlist"] )

if args["batchoutputlist"] != "" or args["batchoutputenum"] != "" or args["eval"]:
    # adjust hi-level params for a no-show "batch output" run
    b_gui = False
    b_show = False
    b_preload = False
    f_scoredelay = 0.0
    g.frameDelay = False
    g.playOn = True

if args["batchdbpathfn"] != "":
    s_batch_db_pathfn = args["batchdbpathfn"]

if args["evaldbpathfn"] != "":
    s_eval_db_pathfn = args["evaldbpathfn"]

if args["eval"]:
    b_eval = True
    b_preload = False
    g.trackingOn = True

if args["evallog"]:
    b_eval_log = True

if args["dir"] == "" and args["file"] == "":
    print 'must run with --dir x/x/ or --file x/x/out.avi'
    sys.exit()

# Initalize Top Level Loop ----------------------------

directoryFactory = DirectoryFactory()

directoryFactory.setRunType(b_play_dir = b_play_dir)

directoryFactory.setData( initDir= init_dir
                         ,fn=FN
                         )

outputFactory = OutputFactory()

outputFactory.setOutputDir(directoryFactory.initDir)

outputFactory.setBatchState( b_batch_output
                            ,i_batch_output_enum
                            ,l_batch_output_list
                            ,s_batch_db_pathfn)

if b_gui:

    gui = GuiC()  

    guiInterface = GuiInterface(gui)

    guiInterface.initGui( playOnVal = g.playOn
                         ,frameDelayVal = g.frameDelay
                        )

display = Display()

display.setInit(showOn=b_show
                ,scoreOff=b_scoreoff
                ,frameResize=b_resize
                ,frameAnnotateFn=b_annotate_fn)

evalFactory = EvalFactory(on=b_eval
                         ,dbPathFn=s_eval_db_pathfn
                         ,bLog=b_eval_log)


#Video Loop: init a new video-file at top --------------

while(True):
    
    frameFactory = FrameFactory()

    frameFactory.setCam(directoryFactory.vidPathFn())

    frameFactory.setFirstN(first_n)

    if b_preload:
        frameFactory.preload()     

    notesFactory = NotesFactory()

    notesFactory.loadMetaLog(directoryFactory.metalogPathFn())

    notesFactory.setFrameLogInput(framelog_pathfn)

    display.setOrientation(notesFactory.getOrientation())

    display.setShowScoring(b_showscoring)

    display.setScoreDisplayObjEnum(i_scoringenum)

    display.reset()

    trackFactory = TrackFactory(on=g.trackingOn)
    
    trackFactory.setInit(ballColor = notesFactory.getBallColor())

    trackFactory.setAlgoEnum(i_algo_enum)

    trackFactory.setTrackTimer(b_output_tracktimer)

    timeFactory = TimeFactory()

    timeFactory.setFrametimeLog(directoryFactory.frametimePathFn())    
    
    timeFactory.setDelay(g.frameDelay)   
    timeFactory.setScoringDelaySecs(f_scoredelay)
    
    timeFactory.setT0()

    evalFactory.updateByVid(frameTotal=timeFactory.getFrameTotal())

    if b_gui:
        
        guiInterface.updateByVid(vidFn=directoryFactory.vidFn()
                                ,compressionType=notesFactory.getCompression()
                                ,frameTotal=frameFactory.getFrameTotal()
                                ,cumTimeTotal=timeFactory.cumTimeTotal()
                                ,avgFrameFps=timeFactory.avgFrameFps()
                                ,trackingOn=g.trackingOn
                                )
    
    if b_test:
        stub.vidByStr(str_test)(frameFactory, timeFactory, directoryFactory, display)

    while(frameFactory.isOpened()):
        
        if b_test:
            stub.frameByStr(str_test)(frameFactory, timeFactory, directoryFactory, display)
        
        # receive cmd data from gui
        timeFactory.setPlay(g.playOn, g.switchAdvanceFrame)
        timeFactory.setDelay(g.frameDelay)
        timeFactory.setDelaySecs(g.delaySecs)
        
        frameFactory.setPlay(g.playOn)
        frameFactory.setAdvanceFrame(g.switchAdvanceFrame)
        frameFactory.setRetreatFrame(g.switchRetreatFrame)
        frameFactory.setRewind(g.switchRewind)
        frameFactory.setFastforward(g.switchFastforward)

        trackFactory.setCmd(trackingOn=g.trackingOn
                           ,outputParams=g.switchOutputParams
                           ,alterParams=g.switchAlterParams
                           ,resetParams=g.switchResetParams)

        display.setCmd(cmdSelectZoom=g.switchZoom
                      ,cmdSelectRoiMain=g.switchRoiMain
                      ,cmdSelectRoiZoom=g.switchRoiZoom
                      ,trackObjEnum=g.trackObjEnum
                      ,trackTypeEnum=g.trackTypeEnum
                      ,windowTwo=g.windowTwo
                      ,windowThree=g.windowThree
                      ,annotateObjEnum=g.annotateObjEnum
                      ,cmdSelectReset=g.switchSelectReset)

        notesFactory.setCmd( switchOverideNote=g.switchOverideNote)

        outputFactory.setCmd(duplicatesEnum=g.duplicatesEnum
                            ,initWriteVid=g.initWriteVid
                            ,compressionEnum=g.compressionEnum
                            ,writevidOn=g.writevidOn
                            ,switchWriteFrame=g.switchWriteVid
                            ,switchWriteScoring=g.switchWriteScoring
                            ,switchOverideNote=g.switchOverideNote
                            ,switchOutputState=g.switchOutputState
                            ,switchDeleteState=g.switchDeleteState
                            )

        # output, handle before next frame
        if outputFactory.checkWriteVid():
            
            outputFactory.initVidWriter(frameFactory.getFrameSize()
                                        ,directoryFactory.vidFn())
            
            outputFactory.resetFramesData()
            outputFactory.resetFramesInd()
            
            if b_gui:
                guiInterface.update(writevidFn = outputFactory.getWritevidFn())

        
        outputFactory.setWriteFrameCmd(frameFactory.checkWriteFrame())
        if outputFactory.checkWriteFrame():
        
            notesFactory.setDisplayScoring(display.getScoring(outputFactory.needScore()))
            
            outputFactory.writeFrame(frame
                                    ,timeFactory.getLagtimeCurrent()
                                    ,notesFactory.getBaseNote()
                                    ,notesFactory.getFrameData() )

            frameFactory.setWriteAndAdvance(outputFactory.getAdvanceFrame())

        if outputFactory.checkOutputState():
            
            outputFactory.outputState( display = display 
                                      ,frameFactory = frameFactory
                                      ,trackFactory = trackFactory 
                                      ,timeFactory = timeFactory
                                      ,notesFactory = notesFactory)
        
        if b_gui:
            guiInterface.update(cvKeypress=display.getKeypress())


        # new frame section
        if frameFactory.queryNewFrame():
            
            ret, frame = frameFactory.getFrame()
            
            timeFactory.setFrameCurrent(frameFactory.getFrameCounter())
            notesFactory.setFrameCurrent(frameFactory.getFrameCounter())
            trackFactory.setFrameInd(frameFactory.getFrameCounter())
            outputFactory.setFrameCounter(frameFactory.getFrameCounter())

            timeFactory.accumAdvanceTime()
            notesFactory.outputFrameNote()

            if b_gui:

                guiInterface.updateByFrame(
                                     frameCurrent=frameFactory.getFrameCounter()
                                    ,cumTimeCurrent=timeFactory.cumTimeCurrent()
                                    ,lagTuple=timeFactory.lagTuple()
                                    ,trackTimer=trackFactory.getTrackTimerDataCurrent()
                                    )
        else:
            ret = False

        
        if ret or trackFactory.getTrackOnChange():

            trackFactory.setFrame(frame)

            trackFactory.setFrameScore(notesFactory.getFrameScoreForTrack())
            
            trackFactory.trackFrame()
            
            display.setTrack(trackScore = trackFactory.getTrackScore())

            if trackFactory.getTrackOnChange():
                display.resetOperators()


        if ret and evalFactory.isOn():
            
            evalFactory.setInputs( 
                             inputScore=notesFactory.getFrameScoreCurrent()
                            ,trackScore=trackFactory.getTrackScore()
                            )
            
            evalFactory.outcomeFrame()
            
        
        if ret and not(trackFactory.getTrackOnChange()):

            display.setFrame(frame)
            display.setAnnotateMsg(directoryFactory.vidFn())
            
            display.setScoring(notesFactory.getFrameScoreCurrent())
            
            timeFactory.setScoringDelay( notesFactory.checkFrameHasScore()
                                        ,display.getShowScoring())

            display.alterFrame()
            display.drawOperators()
            display.drawTrackers()

            display.adjustOrient()
        
        display.show()
        
        if g.callExit:
            break
            
        timeFactory.delayFrame()

        if b_test:
            mock.frameByStr(str_test)(frameFactory, timeFactory, directoryFactory, display)

    if b_test:
        mock.vidByStr(str_test)(frameFactory, timeFactory, directoryFactory, display)
    
    outputFactory.resetFramesInd()
    
    directoryFactory.incrementPlayCounter()

    if outputFactory.checkBatchExit() or evalFactory.checkExit():
        break

    if directoryFactory.checkExit(frameFactory.getFailedLoad()):
        break

    if g.callExit:
        break


cv2.destroyAllWindows()

if b_test:
    mock.exitByStr(str_test)()
    stub.exitByStr(str_test)()    #write to stderr