import cv2
import argparse
import os, sys, time
import numpy as np

# NOTES:

# TODOS:
# track the main diff as in adapt_thresh:
    # true/false there is some diff
    # "big circle" location

#ARGS
default_file = "output13.avi"
default_savedir = "data/write/july2018/"
# default_savedir = "c:/users/wsutt/desktop/files/ppd/ppd/scratch/"

ap = argparse.ArgumentParser()
ap.add_argument("--file", type=str, default=default_file)
ap.add_argument("--show", action="store_true")
ap.add_argument("--save", action="store_true")
ap.add_argument("--savedir", type=str, default=default_savedir)
args = vars(ap.parse_args())

#SAVE/WRITE-OUT
if args["save"]:
    #TODO - make this a module
    i = 0
    files = os.listdir(args["savedir"])
    while(True):
        i += 1
        fn = "testoutput" + str(i)
        fn += ".h264" 
        # fn += ".avi" 
            
        if fn in files:
            continue
        else:
            fourcc = cv2.VideoWriter_fourcc("X","2","6","4")
            # fourcc = cv2.VideoWriter_fourcc("M","P","4"," ")
            # fourcc = -1
            outfps = 30
            outshape = (640,480)
            save_fn = args["savedir"] + fn
            output = cv2.VideoWriter(save_fn,fourcc,outfps,outshape)    
            print '\n saving diff vid: ', str(save_fn), '\n'
            break

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
        frame_diff_color = cv2.cvtColor(frame_diff, cv2.COLOR_GRAY2BGR)
        output.write(frame_diff_color)
    
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
    output.release()
except:
    pass