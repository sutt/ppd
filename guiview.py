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
from modules.GraphicsCV import draw_annotations, resize_img

'''

[x] Add testing stubs/mocks

[ ] Add notesFactory
    [ ] handle orientation with img_rotate

[ ] Add output basic functionality
    [x] naming: proc1.output1.avi...proc2.output1.avi
        [~] uniqueFn modify + tests
    [ ] making a directory
    [x] copy logs
    [ ] set output dir with cmd line flag
    [x] add writeSnap button


BUGS:
    [ ] pauseTime bug - doesn't account for retreat/advance
    [ ] pauseTime - doesn't account for when called with no-delay
    [x] opens on frame1 (not frame0) for pause_on_open

    
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

#CLI Flags ----------------------------------
ap = argparse.ArgumentParser()
ap.add_argument("--dir", type=str, default="")
ap.add_argument("--file", type=str, default="")
ap.add_argument("--nogui",  action="store_true", default=False)
ap.add_argument("--nodelay", action="store_true", default=False)
ap.add_argument("--preload", action="store_true", default=False)
ap.add_argument("--firstN", type=str, default="")
ap.add_argument("--test", type=str, default="")
ap.add_argument("--noshow", action="store_true", default=False)
ap.add_argument("--output", type=str, default="")
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

#Video Loop: init a new video-file at top --------------

while(True):
    
    frameFactory = FrameFactory()

    frameFactory.setCam(directoryFactory.vidPathFn())

    frameFactory.setFirstN(first_n)

    if b_preload:
        frameFactory.preload()     

    timeFactory = TimeFactory()

    timeFactory.setFrametimeLog(directoryFactory.frametimePathFn())    
    
    timeFactory.setDelay(g.frameDelay)   
    
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

        # output, handle before next frame
        if outputFactory.setInitWriteVid(g.initWriteVid):
            outputFactory.initVidWriter(frameFactory.getFrameSize()
                                        ,directoryFactory.vidFn())
            if b_gui:
                guiInterface.update(writevidFn = outputFactory.getWritevidFn())
        
        outputFactory.setWriteFrameOn(g.writevidOn, g.switchWriteVid)
        outputFactory.setWriteFrameCmd(frameFactory.checkWriteFrame())
        if outputFactory.checkWriteFrame():
            outputFactory.writeFrame(frame, timeFactory.getLagtimeCurrent())
        
        if frameFactory.queryNewFrame():
            
            ret, frame = frameFactory.getFrame()
            
            timeFactory.setFrameCurrent(frameFactory.getFrameCounter())

            if b_gui:

                guiInterface.updateByFrame(
                                     frameCurrent=frameFactory.getFrameCounter()
                                    ,cumTimeCurrent=timeFactory.cumTimeCurrent()
                                    ,lagTuple=timeFactory.lagTuple()
                                    )
        else:
            ret = False

        if ret:
            
            imgDisplay = frame.copy()

            if b_resize:
                imgDisplay = resize_img(imgDisplay, True, (640,480))
            
            if b_annotate_fn:
                msg = [directoryFactory.vidFn()]
                imgDisplay = draw_annotations(imgDisplay, msg)

        if b_show:

            windowName = 'img_display'
            cv2.imshow(windowName, imgDisplay)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

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