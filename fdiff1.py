import cv2
import argparse
import os, sys, time
import numpy as np
from vidwriter import VidWriter
from miscutils import uniqueFn


'''
TODOS
[x] insert unqiueFn and VidWriter
[x] change savedir
[ ] need to use lossless compression because its such fine detail
[ ] track the main diff as in adapt_thresh:
    [ ] true/false there is some diff
    [ ] "big circle" location
'''

#ARGS
default_file = "output13.avi"
default_savedir = "data/july2018/misc/"
# default_savedir = "c:/users/wsutt/desktop/files/ppd/ppd/scratch/"

ap = argparse.ArgumentParser()
ap.add_argument("--file", type=str, default=default_file)
ap.add_argument("--show", action="store_true")
ap.add_argument("--save", action="store_true")
ap.add_argument("--savedir", type=str, default=default_savedir)
ap.add_argument("--codec", default="h264")
ap.add_argument("--ext", default = "h264")
args = vars(ap.parse_args())

#SAVE/WRITE-OUT
if args["save"]:
    
    fn = uniqueFn(  fn_base = "diff"
                    ,fn_dir = args["savedir"]
                    ,fn_ext = "avi" #args["ext"]
                    )
    
    vw = VidWriter( savefn = args["savedir"] + fn)
                    # ,fourcc = "x264" #args["codec"]
                    # ,outfps = 50
                    # )

    print '\n saving diff vid: ', args["savedir"] + fn, '\n'


#INIT-INPUT
cap = cv2.VideoCapture(args["file"])
ret, current_frame = cap.read()
previous_frame = current_frame


#LOOP
while(cap.isOpened()):

    #CALC-DIFF
    current_frame_gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
    previous_frame_gray = cv2.cvtColor(previous_frame, cv2.COLOR_BGR2GRAY)    
    frame_diff = cv2.absdiff(current_frame_gray,previous_frame_gray)

    #SAVE
    if args["save"]:
        # frame_diff_color = cv2.cvtColor(frame_diff, cv2.COLOR_GRAY2BGR)
        # vw.write(frame_diff_color)
        vw.write(frame_diff)
    
    #SHOW
    if args["show"]:
        cv2.imshow('frame diff ',frame_diff)      
        time.sleep(0.03)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


    #READ-VID, SET_PREV
    previous_frame = current_frame.copy()
    ret, current_frame = cap.read()

    
#TEAR-DOWN
cap.release()
cv2.destroyAllWindows()
try:
    vw.release()
except:
    pass