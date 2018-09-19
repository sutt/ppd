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
from modules.GraphicsCV import draw_annotations, resize_img

'''

[ ] frameFactory
    [x] frameCounter internalized
    [x] retreatFrame
    [ ] reset global vars


[ ] timeFactory
    [ ] pauseTime

[ ] loop -> gui:
    [x] frame_i
    [x] t=
        [ ] "/out of x"
    [ ] lag intervals

[x] --file function
    [x] it restarts video on play
    [x] it doesn't cycle on pause/advance

[ ] Add preload-flag for dir loop
[ ] Add a no-delay flag
[ ] Add speed-up / slow-down option

BUGS:
    [x] fix --dir loop play
    [x] add requestedCounter and check
        [x] check frame < 0
    [ ] cum time in gui off-by-one
    [ ] after pause + advance/retreat, vid restart from beginning
    [ ] why is reponsiveness so slow?
    [ ] are there misses on loop-action, globals set out of order?


'''

g.init()
g.playOn = True
g.switchAdvanceFrame = False
g.switchRetreatFrame = False

b_play_dir = False
b_preload = True
b_pause_onopen = True
b_delay = True
b_annotate_fn = False
b_resize = True

# init_dir = "data/proc/hello-training-data/"


ap = argparse.ArgumentParser()
ap.add_argument("--nogui",  action="store_true", default=False)
ap.add_argument("--dir", type=str, default="")
ap.add_argument("--file", type=str, default="")
args = vars(ap.parse_args())

if not(args["nogui"]):
    gui = GuiC(b_log=True)  

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

if b_play_dir:
    vidExts = (".avi",)
    list_files = os.listdir(init_dir)
    list_vids = filter(lambda fn: any([ext in fn for ext in vidExts]), list_files)

playCounter = 0


while(True):


    if b_play_dir:
        vidFn = list_vids[playCounter % len(list_vids)]
    else:
        vidFn = FN

    
    frametimeFn = vidFn.split(".")[0] + ".txt"

    cumFrametime = TimeLog().get_cum_time(
                                        os.path.join(init_dir, frametimeFn)
                                        )[1:]

    # pauseTime = timeFactory.getPauseTime()    

    frameFactory = FrameFactory()
    
    frameFactory.setCam(os.path.join(init_dir, vidFn))

    if b_preload:
        frameFactory.preload()        

    if not(args["nogui"]):
        frameFactory.linkGui(gui)

    playCounter += 1
    t_0 = time.time()
    frameCounter = 0
    pauseTime = 0
    
    while(frameFactory.isOpened()):

        
        frameFactory.setPlay(g.playOn)
        
        frameFactory.setAdvanceFrame(g.switchAdvanceFrame)

        frameFactory.setRetreatFrame(g.switchRetreatFrame)
        
        if g.switchAdvanceFrame:
            g.switchAdvanceFrame = False

        if g.switchRetreatFrame:
            g.switchRetreatFrame = False

        if frameFactory.queryNewFrame():
            ret, frame = frameFactory.getFrame()
            frameFactory.updateGui(vidFn=vidFn
                                  ,cumTimeArray=cumFrametime
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

            frameCounter += 1

            if b_delay:
                if frameCounter > len(cumFrametime) - 1:
                    continue
                secsAhead = cumFrametime[frameCounter] - (pauseTime + time.time() - t_0)
                if secsAhead > 0.001:
                    time.sleep(secsAhead - 0.001)

        else:
            
            pass


    print 'end of camera'



cv2.destroyAllWindows()