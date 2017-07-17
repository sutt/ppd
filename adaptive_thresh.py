import os, sys, time
import numpy as np
import cv2
import imutils
from collections import deque
from matplotlib import image as mpimg

from matplotlib import pyplot as plt

from track_a import *

hello()

def transformA(img, blur = 11, b_hsv = False):
    #frame = imutils.resize(frame, width=600)
    out = cv2.GaussianBlur(img, (blur, blur), 0)
    if b_hsv: return cv2.cvtColor(out, cv2.COLOR_BGR2HSV)
    return out    
    
def threshA(img, threshLo = (0,0,0), threshHigh = (255,255,255)):
    return cv2.inRange(out, greenLower, greenUpper)
    
def repairA(img, iterations = 2):
    img = cv2.erode(img, None, iterations=iterations)
    mask = cv2.dilate(img, None, iterations=iteratins)

def create_tracking_frame

vc = cv2.VideoCapture(args["file"])
        while(vc.isOpened()):
            try:
                ret,frame = vc.read()
                if ret:
                    frames.append(frame)
                    j += 1
                else:
                    print 'no ret num: ', str(j)
                    vc.release()
            except Exception as e:
                print 'exception loading frames', e

crop_img(frame, current_tracking_frame)

def main():

    #Init and Params ---------------------------
    cam_params = 0
    h_img, w_img = cam_params[0], cam_params[1]
    
    b_file_vid = False
    b_picamera = False
    b_cv_ccamera = True
    
    if b_file_vid:
        vc = cv2.VideoCapture(args["file"])
    elif b_cv_ccamera:
        vc = cv2.VideoCapture(0)
    else:
        print 'couldnt find a videocam object'

    current_tracking_frame = (0,0,h_img, w_img)
    time_last = time.time()
    b_tracking_frame = False
    b_drawTracking = False
    
    #b_track_success = False

    info_annotations = []

    #Loop --------------------------------------
    # this might have to be different between picam and cv-cam
    # so make the inside of this a function

    while(vc.isOpened()):

        

        if b_cv_ccamera:
            ret, frame = vc.read()
        elif: b_picamera:
            frame = PiCamera()
        elif:
            ret, frame = vc.read()
        
        if not(ret): break

        #if b_agenda:
        #    time_passed = time.time() - time_last
        #    ret_agenda = do_agenda(time_passed)
        
        if b_tracking_frame:
            current_tracking_frame = create_tracking_frame()
            img = crop_img(frame, current_tracking_frame)
        else:
            img = frame

        img_p = transformA(img, b_hsv = False)
        mask = threshA(img_p threshLo = (1,1,1), threshHigh = (254,254,254) )
        mask = repairA(mask, iterations = 2)
        
        # you could also crop after the track to see if there was one within

        #LocateTrack, how many shapes are there?
        x,y,radius = 
        if b_tracking_frame:
            x,y,radius = decrop_track(h_img, w_img)

        #Track successful?
        b_track_success = filter_track()

        #draw onto frame
        img_display = frame

        if b_tracking_frame:
            img_display = draw_tracking_frame(frame)

        if b_drawTracking and b_track_success:
            img_display = draw_tracking(img_display,mask)

        if b_annotate_img:
            img_display = draw_annotations(img_display, info_annotations)

        #Histo processing
        if b_histo:
            ball_vs_background()

        #Show Images
        if b_show_main_img:
            cv2.imshow('img', img_display)
            #plt.imshow(img_display, cvtColor)
        
        if b_show_transformed_img:
            cv2.imshow('the ball',img_p)

        if b_show_tracked_img:
            cv2.imshow('the ball',on_pxs)
        
        #Show Histos
        if b_show_histos:
            pass
            #need to close old ones
            #keep focus on cv windows though?
            #keep window positioning ?

        # Logging
        if b_log:
            pass

        #Options -------------------------------------

    #Cleanup -------------------
    vc.release()
    cv2.destroyAllWindows()
    if args['writebookvideo']: vw.release()