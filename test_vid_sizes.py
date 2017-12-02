import cv2
import time, random
import os, sys
import argparse, traceback
import imutils
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--picsize", type=str, default="")
ap.add_argument("--cam_num", type=str, default="0")
args = vars(ap.parse_args())
cam_num = int(args["cam_num"])

size_params = []
size_params.append( (640,480) )
size_params.append( (1280,720) )
size_params.append( (1280,960) )
size_params.append( (1920,1080) )
outcome = [False] * len(size_params)
i = 0

_fw = cv2.CAP_PROP_FRAME_WIDTH 
_fh = cv2.CAP_PROP_FRAME_HEIGHT
_fps = cv2.CAP_PROP_FPS
_fourcc = cv2.CAP_PROP_FOURCC
_params = [_fw,_fh,_fps,_fourcc]

print 'webcam ', str(cam_num)

for size_param in size_params:
    
    print 'Trying for size: ', str(size_param)

    vc  =  cv2.VideoCapture(cam_num)

    print 'initial get: '
    vc_params = [vc.get(p) for p in _params]
    print vc_params

    try:
        vc.set(3,size_param[0])
        vc.set(4,size_param[1])
    except:
        print 'couldnt set vc with size_params'

    print 'second get: '
    vc_params = [vc.get(p) for p in _params]
    print vc_params


    while(vc.isOpened()):

        ret,frame = vc.read()  
        if ret:
            out_shape = frame.shape
            print 'Shape: ', str(out_shape)

            if (out_shape[0] == size_param[1]) and \
            (out_shape[1] == size_param[0]):
                print 'SUCCESS'
                outcome[i] = True
            else:
                print 'FAIL'
        else:
            print 'ret=False'

        break

    vc.release()
    i += 1

print 'end'
for i in range(len(size_params)):
    print str(size_params[i]), ' ', str(outcome[i])