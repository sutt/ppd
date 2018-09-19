import os, sys, time
import numpy as np
import cv2
import argparse
import modules.GlobalsC as g
from miscutils import uniqueFn
from vidwriter import VidWriter
from modules.GuiC import GuiC
from modules.Utils import TimeLog
from modules.Utils import MetaDataLog
from modules.ControlFlow import FrameFactory
from modules.ControlFlow import TimeFactory
from modules.GraphicsCV import draw_annotations, resize_img

'''

[x] frameFactory
    [x] frameCounter internalized
    [x] retreatFrame
    [x] reset global vars


[x] timeFactory
    [x] pauseTime
        [ ] pauseTime bug - doesn't account for retreat/advance
        [ ] doesn't account for when called with no-delay

[x] handle err when no framelog
[ ] pause on 1st frame after open
[x] init play button color, other gui vars
    [x] delay radio button

[ ] loop -> gui:
    [x] frame_i
    [x] t=
        [x] "/out of x"
    [ ] lag intervals
    [ ] avg FPS

[x] --file function
    [x] it restarts video on play
    [x] it doesn't cycle on pause/advance

[ ] Add preload-flag for dir loop
[x] Add a no-delay flag
[x] Add a no-delay radio button
[ ] Add slow-down option: a factor

BUGS:
    [x] fix --dir loop play
    [x] add requestedCounter and check
        [x] check frame < 0
    [x] cum time in gui off-by-one
    [ ] random crashes during puase+adavanceframe-held-down; hard to replicate??
    [ ] after pause + advance/retreat, vid restart from beginning
    [ ] why is reponsiveness so slow?
    [ ] are there misses on loop-action, globals set out of order?


'''

#Globals---------------------------------
# carry info from gui -> mainloop
g.init()
g.playOn = True
g.switchAdvanceFrame = False
g.switchRetreatFrame = False
g.frameDelay = True

#High Level Options --------------------------
b_play_dir = False
b_preload = True
b_pause_onopen = True
b_annotate_fn = False
b_resize = True
b_gui = True

#CLI Flags ----------------------------------
ap = argparse.ArgumentParser()
ap.add_argument("--dir", type=str, default="")
ap.add_argument("--file", type=str, default="")
ap.add_argument("--nogui",  action="store_true", default=False)
ap.add_argument("--nodelay", action="store_true", default=False)
ap.add_argument("--preload", action="store_true", default=False)
args = vars(ap.parse_args())


#Run Type: sets options ----------------------

if args["file"] != "":
    PATH_FN = args["file"]
    PATH, FN = os.path.split(PATH_FN)
    init_dir = os.path.realpath(PATH)
    b_preload = True
    
    
if args["dir"] != "":
    b_play_dir = True
    b_preload = False
    init_dir = os.path.realpath(args["dir"])
    b_annotate_fn = True
    b_resize = True
    g.frameDelay = False

if args["nogui"]:
    b_gui = False

if args["nodelay"]:
    g.frameDelay = False

if args["preload"]:
    b_preload = True


#TODO - add this to directoryFactory
if b_play_dir:
    vidExts = (".avi",)
    list_files = os.listdir(init_dir)
    list_vids = filter(lambda fn: any([ext in fn for ext in vidExts]), list_files)


if b_gui:
    gui = GuiC()  

    gui.myGui.initGui(playOn = g.playOn
                     ,frameDelay = g.frameDelay
                     )


#Video Loop: init a new video-file at the top of this loop
playCounter = 0

while(True):


    #TODO - add to directoryFactory
    if b_play_dir:
        vidFn = list_vids[playCounter % len(list_vids)]
    else:
        vidFn = FN

    #TODO - put this in class    
    frametimeFn = vidFn.split(".")[0] + ".txt"
    
    timeFactory = TimeFactory()

    timeFactory.setFrametimeLog(logPathFn=os.path.join(init_dir, frametimeFn))

    timeFactory.setDelay(g.frameDelay)

    frameFactory = FrameFactory()
    
    frameFactory.setCam(os.path.join(init_dir, vidFn))

    if b_preload:
        frameFactory.preload()        

    if b_gui:
        frameFactory.linkGui(gui)

    playCounter += 1
    
    timeFactory.setT0()

    
    while(frameFactory.isOpened()):

        
        frameFactory.setPlay(g.playOn)
        frameFactory.setAdvanceFrame(g.switchAdvanceFrame)
        frameFactory.setRetreatFrame(g.switchRetreatFrame)
        
        timeFactory.setPlay(g.playOn)
        timeFactory.setDelay(g.frameDelay)
        
        if frameFactory.queryNewFrame():
            
            ret, frame = frameFactory.getFrame()
            
            timeFactory.setFrameCurrent(frameFactory.getFrameCounter())

            frameFactory.updateGui(vidFn=vidFn
                                  ,cumTimeCurrent=timeFactory.cumTimeCurrent()
                                  ,cumTimeTotal=timeFactory.cumTimeTotal()
                                  )
        else:
            continue

        if ret:
            
            imgDisplay = frame.copy()

            if b_resize:
                imgDisplay = resize_img(imgDisplay, True, (640,480))
            
            if b_annotate_fn:
                msg = [vidFn]
                imgDisplay = draw_annotations(imgDisplay, msg)

            windowName = 'img_display'  #TODO - change window if not resize

            cv2.imshow(windowName, imgDisplay)
                        
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            timeFactory.delayFrame()

        else:
            
            pass


    print 'end of camera'



cv2.destroyAllWindows()