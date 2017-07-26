import os, sys, time, copy, random, argparse
import traceback
import numpy as np
import cv2
import imutils
from collections import deque
from matplotlib import image as mpimg
from matplotlib import pyplot as plt

from Camera import initCam, setupCam, getFrame
from GraphicsA import LiveHist
from Methods import InitLiveHist, SwitchYLim
from GraphicsCV import draw_tracking_frame, draw_tracking, draw_annotations
from GraphicsCV import ShowImages
from ImgUtils import px3clr_3px1clr, px_to_list, px_remove_crop, crop_img
from ImgProcs import threshA, transformA, repairA
from TrackA import find_xy, find_radius
from Methods import imgToPx, pxToHist
#from MiscUtils import hist_from_img, create_tracking_frame
#from MiscUtils import mock_gaussian, rand_gauss_params, mock_hist_data

ap = argparse.ArgumentParser()
ap.add_argument("--file", type=str, default="fps30.h264")
ap.add_argument("--showhisto", action="store_true")
ap.add_argument("--showbackghisto", action="store_true")
ap.add_argument("--printlog", action="store_true")
args = vars(ap.parse_args())


def main():

    #INIT & PARAMS
    b_tracking_frame = True
    b_histo = args["showhisto"]     
    b_hist_rect = True
    b_show_histos = args["showhisto"]  
    b_histo_backg = args["showbackghisto"]
    b_drawTracking = True
    b_print_log = args["printlog"]

    hist_update_hz = 1
    waitKeyRefresh = 1
    current_tracking_frame = ((100,100),(200,200))

    switch_new_ylim = True  
    time_last = time.time()
    info_annotations = []
    livehist = None

    cam_params = (640,480)
    h_img, w_img = cam_params[0], cam_params[1]
    cam_type = 'cv_cam'   # 'pi_cam','file_cam'

    vc = initCam(cam_type)
    vc = setupCam(vc, cam_type = cam_type, params = cam_params)

    while(vc.isOpened()):

        ret, frame = getFrame(vc, cam_type = 'cv_cam')        
        if not(ret): break

        # THRESHOLD MASK
        img_t = transformA(frame.copy(), b_hsv = True)
        Lo, Hi = (29, 86, 6), (64, 255, 255)
        img_mask = threshA(img_t, threshLo = Lo , threshHi = Hi )
        img_mask = repairA(img_mask, iterations = 2)
        
        # LOCATE / TRACK
        x,y = find_xy(img_mask)
        radius = find_radius(img_mask)
        
        # FILTER TRACK
        b_track_success = True

        #DRAW ONTO FRAME
        img_display = frame

        if b_tracking_frame:
            img_display = draw_tracking_frame(frame,x,y,radius)

        if b_drawTracking:
            img_display = draw_tracking(img_display,current_tracking_frame)

        b_annotate_img = False
        if b_annotate_img:
            img_display = draw_annotations(img_display, info_annotations)       
            

        # PROC & SHOW HISTOS
        if b_show_histos:
            
            if livehist == None:
                livehist = InitLiveHist(b_histo_backg)
                last_hist_update = time.time() - (hist_update_hz + 1)    #and process
            
            if time.time() - last_hist_update > hist_update_hz:

                if b_histo:
                    px_data = imgToPx(img_t, current_tracking_frame, ) ##frame should be img
                    hist_data = pxToHist(px_data)
                
                if switch_new_ylim:
                    SwitchYLim(livehist, hist_data)
                    switch_new_ylim = False

                livehist.update_figure( hist_data
                            ,ax_ind = range(livehist.N)
                            ,frames = 1
                            ,show = True
                            ,epsilon = .0001)
                
                last_hist_update = time.time()
 
        #SHOW IMAGES
        ShowImages(  display_img = True,   img_d = img_display
                    ,transform_img = True, img_t = img_t
                    ,mask_img = True,      img_m = img_mask )
        

        if cv2.waitKey(waitKeyRefresh)== ord('q'):
            print 'quitting'
            break
        
        if cv2.waitKey(waitKeyRefresh) == ord('o'):
    
            # options -----------------
            while(True):
                ret = raw_input('options ... show_histo, hide_histo, new_tracking_frame x0 y0 x1 y1, quit \n>')                

                if ret == 'quit':
                    break

                elif ret[:10] == "show_histo":
                    b_show_histos = True
                    b_histo = True
                
                elif ret[:10] == "hide_histo":
                    b_show_histos = False
                    b_histo = False

                elif ret[:18] == "new_tracking_frame":
                    
                    opt_args = ret.split(' ')
                    if len(opt_args) > 1:
                        try:
                            x0,y0,x1,y1 = int(opt_args[1]), int(opt_args[2]),  int(opt_args[3]), int(opt_args[4])
                            current_tracking_frame = ((x0,y0),(x1,y1))
                            print 'changing tracking_frame to: ', str(current_tracking_frame)
                            switch_new_ylim = True
                            print 'switching rect hist ylim'
                        except:
                            print 'could not set tracking_frame.'    
                    else:
                        print 'did not recognize length of tracking_frame input.'

                else:
                    print 'option <', str(ret),  '> not recognized'
            
            print 'quitting options...'
            # /options ----------------


        # DELAY FPS
        # if cam_type == 'file_cam':
        #     if b_slow_for_fps:
        #         current_frames_time = time.time() - time_last_frame 
        #         sleep_time = current_frames_time - fps_time - epsilon_fps_time
        #         if sleep_time > 0:
        #             time.sleep(sleep_time)
        #         time_last_frame = time.time()
        
        # LOGGING
        if b_print_log:
            print 'frame time: %.2f' % (time.time() - time_last)
            time_last = time.time()

        #Options -------------------------------------

    #Cleanup -------------------
    vc.release()
    cv2.destroyAllWindows()
    #if args['writebookvideo']: vw.release()

main()
print 'exiting main'