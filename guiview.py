import numpy as np
import cv2
import argparse
import os, sys, time
from miscutils import uniqueFn
from vidwriter import VidWriter
import modules.GlobalsC as g
from modules.GuiC import GuiC
from modules.GraphicsCV import resize_img
from modules.Utils import TimeLog
from modules.Utils import MetaDataLog
from modules.GraphicsCV import draw_annotations, resize_img
'''

[ ] frameFactory
[ ] pauseTime

'''

g.init()
g.playOn = True
g.switchAdvanceFrame = False

b_play_dir = False
b_preload = True
b_pause_onopen = True
init_dir = "data/proc/hello-training-data/"
b_delay = True
b_annotate_fn = False

ap = argparse.ArgumentParser()
ap.add_argument("--nogui",  action="store_true", default=False)
ap.add_argument("--dir", type=str, default="")
args = vars(ap.parse_args())

if not(args["nogui"]):
    gui = GuiC(b_log=True)  


if args["dir"] != "":
    b_play_dir = True
    b_preload = False
    init_dir = args["dir"]
    b_annotate_fn = True
    b_resize = True


if b_play_dir:
    vidExts = (".avi")
    list_files = os.listdir(init_dir)
    list_vids = filter(lambda fn: any([ext in fn for ext in vidExts]), list_files)

play_counter = 0

while(True):

    FN = "output4"
    EXT = "avi"
    
    vidFn = (FN + "." + EXT)

    if b_play_dir:
        vidFn = list_vids[play_counter % len(list_vids)]

    frametimeFn = vidFn.split(".")[0] + ".txt"

    cumFrametime = TimeLog().get_cum_time(
                                        os.path.join(init_dir, frametimeFn)
                                        )[1:]

    cam = cv2.VideoCapture(os.path.join(init_dir, vidFn))

    if b_preload:
        preloaded_frames = preloadFromCam(cam)

    play_counter += 1

    t_0 = time.time()
    frameCounter = 0
    bOneFrame = False
    pauseTime = 0
    
    while(cam.isOpened() or b_preload):

        bNewFrame = False

        if g.playOn or bOneFrame:

            ret,frame = cam.read()

            bNewFrame = True
            
            bOneFrame = False

        if g.switchAdvanceFrame:
            g.switchAdvanceFrame = False
            bOneFrame = True
            #TODO - set pauseTime
            continue

        if ret:
            
            if not(bNewFrame):
                continue

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
            
            cam.release()

                



cv2.destroyAllWindows()