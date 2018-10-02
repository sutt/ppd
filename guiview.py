import os, sys, time
import numpy as np
import cv2
import argparse
import modules.GlobalsC as g
from miscutils import uniqueFn
from vidwriter import VidWriter
from modules.GuiC import GuiC
from modules.GuiC import GuiInterface
from modules.Utils import TimeLog
from modules.Utils import MetaDataLog
from modules.ControlFlow import DirectoryFactory
from modules.ControlFlow import FrameFactory
from modules.ControlFlow import TimeFactory
from modules.ControlFlow import OutputFactory
from modules.ControlFlow import NotesFactory
from modules.ControlDisplay import Display
from modules.GraphicsCV import (draw_annotations, resize_img, draw_text)

if False: from cv2 import *  # for vscode intellisense

'''

[x] Add notesFactory
    [x] handle orientation with img_rotate
    [x] handle scoring data

[ ] controls
    [x] button: write frame + frame-data + frame-scoring [ + advanceFrame]
    [ ] compression radio button
    
    [ ] refactor gui to make
        [ ] does this enable debugging better?
    
    [ ] keypress basic

[ ] functionality
    [ ] i/o images
    [ ] write to an existing video
    [ ] delete frame(s) from a video via script:
    [ ] semi-preload; streaming
        [ ] default for files_size * 25(?) > 1.5BG
    [ ] filter videos played via metalog props
    [ ] filter frames played via metalog props

BUGS:
    [ ] pauseTime bug - doesn't account for retreat/advance
    [ ] pauseTime - doesn't account for when called with no-delay
    [x] opens on frame1 (not frame0) for pause_on_open
    [ ] add other file extensions for vids
    [ ] new video resets outputFactory (?) and thus resets metalog when video is refreshed 

    
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
g.windowThree = False
g.switchWriteScoring = False


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
f_scoredelay = 1.0

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

# Initalize Top Level Loop ----------------------------

directoryFactory = DirectoryFactory()

directoryFactory.setRunType(b_play_dir = b_play_dir)

directoryFactory.setData( initDir= init_dir
                         ,fn=FN
                         )

outputFactory = OutputFactory()

outputFactory.setOutputDir(directoryFactory.initDir)

if b_gui:

    gui = GuiC()  

    guiInterface = GuiInterface(gui)

    guiInterface.initGui( playOnVal = g.playOn
                         ,frameDelayVal = g.frameDelay
                        )

display = Display()

display.setInit(showOn=b_show
                ,frameResize=b_resize
                ,frameAnnotateFn=b_annotate_fn)

#Video Loop: init a new video-file at top --------------

while(True):
    
    frameFactory = FrameFactory()

    frameFactory.setCam(directoryFactory.vidPathFn())

    frameFactory.setFirstN(first_n)

    if b_preload:
        frameFactory.preload()     

    notesFactory = NotesFactory()

    notesFactory.loadMetaLog(directoryFactory.metalogPathFn())

    notesFactory.setFrameLog(framelog_pathfn)

    notesFactory.setShowScoring(b_showscoring)

    display.setOrientation(notesFactory.getOrientation())

    timeFactory = TimeFactory()

    timeFactory.setFrametimeLog(directoryFactory.frametimePathFn())    
    
    timeFactory.setDelay(g.frameDelay)   
    timeFactory.setScoringDelaySecs(f_scoredelay)
    
    timeFactory.setT0()

    if b_gui:
        
        guiInterface.updateByVid(vidFn=directoryFactory.vidFn()
                                ,frameTotal=frameFactory.getFrameTotal()
                                ,cumTimeTotal=timeFactory.cumTimeTotal()
                                ,avgFrameFps=timeFactory.avgFrameFps()
                                )
    
    if b_test:
        stub.vidByStr(str_test)(frameFactory, timeFactory, directoryFactory)

    while(frameFactory.isOpened()):
        
        if b_test:
            stub.frameByStr(str_test)(frameFactory, timeFactory, directoryFactory)
        
        # receive cmd data from gui
        frameFactory.setPlay(g.playOn)
        frameFactory.setAdvanceFrame(g.switchAdvanceFrame)
        frameFactory.setRetreatFrame(g.switchRetreatFrame)
        frameFactory.setRewind(g.switchRewind)
        frameFactory.setFastforward(g.switchFastforward)
        
        timeFactory.setPlay(g.playOn)
        timeFactory.setDelay(g.frameDelay)
        timeFactory.setDelaySecs(g.delaySecs)

        display.setCmd(cmdSelectZoom=g.switchZoom
                      ,cmdSelectRoiMain=g.switchRoiMain
                      ,cmdSelectRoiZoom=g.switchRoiZoom
                      ,windowTwo=g.windowTwo
                      ,windowThree=g.windowThree)

        # output, handle before next frame
        if outputFactory.setInitWriteVid(g.initWriteVid):
            
            outputFactory.initVidWriter(frameFactory.getFrameSize()
                                        ,directoryFactory.vidFn())
            
            notesFactory.resetFramesData()
            
            if b_gui:
                guiInterface.update(writevidFn = outputFactory.getWritevidFn())
        
        outputFactory.setWriteFrameOn(g.writevidOn, g.switchWriteVid, 
                                      g.switchWriteScoring)
        
        outputFactory.setWriteFrameCmd(frameFactory.checkWriteFrame())
        
        if outputFactory.checkWriteFrame():
        
            notesFactory.setScoring(display.getScoring(outputFactory.needScore()))
        
            outputFactory.writeFrame(frame
                                    ,timeFactory.getLagtimeCurrent()
                                    ,notesFactory.getNotesCurrent() )
        
        if frameFactory.queryNewFrame():
            
            ret, frame = frameFactory.getFrame()
            
            timeFactory.setFrameCurrent(frameFactory.getFrameCounter())

            notesFactory.setFrameCurrent(frameFactory.getFrameCounter())

            if b_gui:

                guiInterface.updateByFrame(
                                     frameCurrent=frameFactory.getFrameCounter()
                                    ,cumTimeCurrent=timeFactory.cumTimeCurrent()
                                    ,lagTuple=timeFactory.lagTuple()
                                    )
        else:
            ret = False

        if ret:
            
            display.setFrame(frame)
            display.setAnnotateMsg(directoryFactory.vidFn())
            
            display.setScoring(notesFactory.getFrameScoreCurrent())
            timeFactory.setScoringDelay(notesFactory.getFrameScoreCurrent())
            
            display.alterFrame()
            display.drawOperators()
        
        display.show()
        
        if g.callExit:
            break
            
        timeFactory.delayFrame()

        if b_test:
            mock.frameByStr(str_test)(frameFactory, timeFactory, directoryFactory)

    if b_test:
        mock.vidByStr(str_test)(frameFactory, timeFactory, directoryFactory)
    
    directoryFactory.incrementPlayCounter()

    if directoryFactory.checkExit(frameFactory.getFailedLoad()):
        break

    if g.callExit:
        break


cv2.destroyAllWindows()

if b_test:
    mock.exitByStr(str_test)()
    stub.exitByStr(str_test)()    #write to stderr