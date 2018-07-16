import cv2
import argparse
import os, sys, time
import numpy as np

# NOTES:
# need to put h264.dll in path, specifically in scratch/
# h264 is worse than avi correct?
# is this validated by smaller file size?
# is this what happens when ball appears not to move b/w several frames?


# TODOS:
# write out diffs
# track the main diff as in adapt_thresh:
    # true/false there is some diff
    # "big circle" location

ap = argparse.ArgumentParser()
default_vid = "../output13.avi"
ap.add_argument("--file", type=str, default=default_vid)
args = vars(ap.parse_args())

cap = cv2.VideoCapture(args["file"])

ret, current_frame = cap.read()
previous_frame = current_frame


while(cap.isOpened()):

    current_frame_gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
    previous_frame_gray = cv2.cvtColor(previous_frame, cv2.COLOR_BGR2GRAY)    

    frame_diff = cv2.absdiff(current_frame_gray,previous_frame_gray)

    cv2.imshow('frame diff ',frame_diff)      
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    previous_frame = current_frame.copy()
    ret, current_frame = cap.read()

    time.sleep(0.03)

cap.release()
cv2.destroyAllWindows()