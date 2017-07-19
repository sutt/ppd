import os, sys, time, copy
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
    return cv2.inRange(img, threshLo, threshHi)
    
def repairA(img, iterations = 2):
    img = cv2.erode(img, None, iterations=iterations)
    img = cv2.dilate(img, None, iterations=iterations)
    return img



def crop_img(img, current_tracking_frame):
    x,y,w,h = current_tracking_frame[0], current_tracking_frame[1], current_tracking_frame[2], current_tracking_frame[3]
    return img[x:x+w,h:h+w,:]    

def draw_tracking_frame(frame, x,y,radius):
    print 'in here'
    #return frame
    cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 10)
    return frame

def initCam(cam_type,**kwargs):
    if cam_type == 'cv_cam': 
            return cv2.VideoCapture(kwargs.get('usb_num',0) )
    elif cam_type == 'pi_cam': 
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
        elif cam_type == 'pi_cam': 
            return True, inp_cam
        elif cam_type == 'file_cam': 
            return inp_cam.read()
        else:
            print 'No frame read possible.'
        
def showImages(img_display,**kwargs):
    if kwargs.get('b_show_main_img', False):
        cv2.imshow('display image', img_display)
        #plt.imshow(img_display, cvtColor)
    
    if kwargs.get('b_show_transformed_img', False):
        cv2.imshow('transformed image', kwargs.get('img_p',None) )

    if kwargs.get('b_show_tracked_img', False):
        cv2.imshow('the ball',kwargs.get('on_pxs',None))

    # if cv2.waitKey(1)== ord('q'):
    #         return 1
    return 0

def create_tracking_frame(**kwargs):
    return (0,0,1,1)

def main():

    #Init and Params ---------------------------
    cam_params = (640,480)
    h_img, w_img = cam_params[0], cam_params[1]
    refresh = 1
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

        
        ret, frame = getFrame(vc, cam_type = 'cv_cam')        
        if not(ret): break

        #if b_agenda:
        #    time_passed = time.time() - time_last
        #    ret_agenda = do_agenda(time_passed)
        
        #note: need to copy() numpy objects for not pass by ref
        b_tracking_frame_2 = False
        if b_tracking_frame_2:
            current_tracking_frame = create_tracking_frame()
            img = crop_img(frame, current_tracking_frame)
        else:
            img = frame[:,:,:]

        img_p = transformA(img, b_hsv = True)
        Lo, Hi = (29, 86, 6), (64, 255, 255)
        mask = threshA(img_p, threshLo = Lo , threshHi = Hi )
        mask = repairA(mask, iterations = 2)
        
        # # you could also crop after the track to see if there was one within

        # #LocateTrack, how many shapes are there?
        x,y = find_xy(mask)
        radius = find_radius(mask)
        print x, ' ', y, ' ', radius
        # if b_tracking_frame:
        #     x,y,radius = decrop_track(h_img, w_img)

        # #Track successful?
        # b_track_success = filter_track()
        b_track_success = True

        #draw onto frame
        img_display = frame

        b_tracking_frame = True
        #b_tracking_frame = False
        if b_tracking_frame:
            img_display = draw_tracking_frame(frame,x,y,radius)
        
        #cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 10)

        # if b_drawTracking and b_track_success:
        #     img_display = draw_tracking(img_display,mask)

        # if b_annotate_img:
        #     img_display = draw_annotations(img_display, info_annotations)

        # #Histo processing
        # if b_histo:
        #     ball_vs_background()

        #Show Images
        #ret = showImages(frame, b_show_main_img = True)
        ret = showImages(img_display, b_show_main_img = True)
        # if ret == 1:
        #     break
        if cv2.waitKey(refresh)== ord('q'):
            print 'quitting'
            break
        #Show Histos
        # if b_show_histos:
        #     pass
            #need to close old ones
            #keep focus on cv windows though?
            #keep window positioning ?
        
        #Delay fps
        # if cam_type == 'file_cam':
        #     if b_slow_for_fps:
        #         current_frames_time = time.time() - time_last_frame 
        #         sleep_time = current_frames_time - fps_time - epsilon_fps_time
        #         if sleep_time > 0:
        #             time.sleep(sleep_time)
        #         time_last_frame = time.time()
        # # Logging
        # if b_log:
        #     pass

        #Options -------------------------------------

    #Cleanup -------------------
    vc.release()
    cv2.destroyAllWindows()
    #if args['writebookvideo']: vw.release()

main()
print 'exiting main'