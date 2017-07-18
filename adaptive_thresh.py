import os, sys, time
import traceback
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
    
def threshA(img, threshLo = (0,0,0), threshHi = (255,255,255)):
    return cv2.inRange(out, threshLo, threshHi)
    
def repairA(img, iterations = 2):
    img = cv2.erode(img, None, iterations=iterations)
    mask = cv2.dilate(img, None, iterations=iterations)

def create_tracking_frame():
    pass

def crop_img(img, current_tracking_frame):
    x,y,w,h = current_tracking_frame[0], current_tracking_frame[1], current_tracking_frame[2], current_tracking_frame[3]
    return img[x:x+w,h:h+w,:]    

def initCam(cam_type,**kwargs):
    if cam_type == 'cv_cam': 
            return cv2.VideoCapture(kwargs.get('usb_num'),0)
        elif cam_type == 'pi_cam: 
            return 1
        elif cam_type == 'file_cam': 
            return  cv2.VideoCapture(kwargs.get('vid_file'),'')
        else:
            print 'No cam object creatable.'

def setupCam(vc, cam_type, params):
    # set ISO, shutter speed, fps, etc...
    try:
        pass
    except Exception as e:
        print 'Could not set cam params: ', str(e)
        print traceback.format_exc()
    return vc

def getFrame(inp_cam, cam_type):
        if cam_type == 'cv_cam': 
            return inp_cam.read()
        elif cam_type == 'pi_cam: 
            return True, inp_cam
        elif cam_type == 'file_cam': 
            return inp_cam.read()
        else:
            print 'No frame read possible.'
        

def main():

    #Init and Params ---------------------------
    cam_params = 0
    h_img, w_img = cam_params[0], cam_params[1]
    
    cam_type = 'cv_cam'     # 'pi_cam' 'file_cam'
    
    vc = initCam(cam_type)
    vc = setupCam(vc, cam_type = cam_type, params = cam_params)

    current_tracking_frame = (0,0,h_img, w_img)

    b_tracking_frame = False
    b_drawTracking = False
    #b_track_success = False

    time_last = time.time()

    info_annotations = []

    #Loop --------------------------------------
    # this might have to be different between picam and cv-cam
    # so make the inside of this a function

    while(vc.isOpened()):

        
        ret, frame = getFrame(vc, type = 'cv_cam')        
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
        
        #Delay fps
        if cam_type = 'file_cam':
            if b_slow_for_fps:
                current_frames_time = time.time() - time_last_frame 
                sleep_time = current_frames_time - fps_time - epsilon_fps_time
                if sleep_time > 0:
                    time.sleep(sleep_time)
                time_last_frame = time.time()
        # Logging
        if b_log:
            pass

        #Options -------------------------------------

    #Cleanup -------------------
    vc.release()
    cv2.destroyAllWindows()
    if args['writebookvideo']: vw.release()