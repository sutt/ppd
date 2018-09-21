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
from modules.GraphicsCV import draw_annotations, resize_img

'''

[x] validate lag interval with sync-framerate ipynb study videos
    --file data/books/correspond-frame-to-framelog/output82.avi

[ ] add 5x/10x increment/decremnt buttons

[ ] Add notesFactory
    [ ] handle orientation with img_rotate

[ ] Add output basic functionality
    [ ] naming: proc1.output1.avi...proc2.output1.avi
        [ ] uniqueFn modify + tests
    [ ] making a directory
    [ ] copy logs
    [ ] set output dir with cmd line flag


BUGS:
    [ ] pauseTime bug - doesn't account for retreat/advance
    [ ] pauseTime - doesn't account for when called with no-delay
    [x] opens on frame1 (not frame0) for pause_on_open

    
'''

#Globals---------------------------------
# carry info from gui -> mainloop
g.init()
g.playOn = True
g.switchAdvanceFrame = False
g.switchRetreatFrame = False
g.frameDelay = True
g.callExit = False
g.delaySecs = 0.0

#High Level Options --------------------------
b_play_dir = False
b_preload = True
b_annotate_fn = False
b_resize = True
b_gui = True
first_n = 0

#CLI Flags ----------------------------------
ap = argparse.ArgumentParser()
ap.add_argument("--dir", type=str, default="")
ap.add_argument("--file", type=str, default="")
ap.add_argument("--nogui",  action="store_true", default=False)
ap.add_argument("--nodelay", action="store_true", default=False)
ap.add_argument("--preload", action="store_true", default=False)
ap.add_argument("--firstN", type=str, default="")
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


if args["nogui"]:
    b_gui = False

if args["nodelay"]:
    g.frameDelay = False

if args["preload"]:
    b_preload = True

if args["firstN"] != "":
    first_n = int(args["firstN"])


# Initalize Top Level Loop ----------------------------

directoryFactory = DirectoryFactory()

directoryFactory.setRunType(b_play_dir = b_play_dir)

directoryFactory.setData( initDir= init_dir
                         ,fn=FN
                         )

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

    while(frameFactory.isOpened()):
        
        frameFactory.setPlay(g.playOn)
        frameFactory.setAdvanceFrame(g.switchAdvanceFrame)
        frameFactory.setRetreatFrame(g.switchRetreatFrame)
        
        timeFactory.setPlay(g.playOn)
        timeFactory.setDelay(g.frameDelay)
        timeFactory.setDelaySecs(g.delaySecs)
        
        if frameFactory.queryNewFrame():
            
            ret, frame = frameFactory.getFrame()
            
            timeFactory.setFrameCurrent(frameFactory.getFrameCounter())

            if b_gui:

                guiInterface.updateGui(vidFn=directoryFactory.vidFn()
                                    ,frameCurrent=frameFactory.getFrameCounter()
                                    ,frameTotal=frameFactory.getFrameTotal()
                                    ,cumTimeCurrent=timeFactory.cumTimeCurrent()
                                    ,cumTimeTotal=timeFactory.cumTimeTotal()
                                    ,avgFrameFps=timeFactory.avgFrameFps()
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


        windowName = 'img_display'
        cv2.imshow(windowName, imgDisplay)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        if g.callExit:    
            cv2.destroyAllWindows()
            sys.exit()

        timeFactory.delayFrame()


    directoryFactory.incrementPlayCounter()

    if directoryFactory.checkExit(frameFactory.getFailedLoad()):
        break


cv2.destroyAllWindows()
