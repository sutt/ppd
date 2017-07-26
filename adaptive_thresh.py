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
from GraphicsCV import draw_tracking_frame, draw_tracking, draw_annotations
from GraphicsCV import showImages
from ImgUtils import px3clr_3px1clr, px_to_list, px_remove_crop, crop_img
from ImgProcs import threshA, transformA, repairA
from TrackA import find_xy, find_radius
from Methods import InitLiveHist
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
    b_tracking_frame_2 = False
    b_histo = args["showhisto"]     
    b_hist_rect = True
    b_show_histos = args["showhisto"]  
    b_show_backg_histos = args["showbackghisto"]
    b_mock_hist_data = False
    b_drawTracking = True
    b_print_log = args["printlog"]

    ylim_padding_mult = 1.0
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

        if b_tracking_frame_2:
            current_tracking_frame = create_tracking_frame()
            img = crop_img(frame, current_tracking_frame)
        else:
            img = frame[:,:,:]

        # THRESHOLD MASK
        img_t = transformA(img, b_hsv = True)
        Lo, Hi = (29, 86, 6), (64, 255, 255)
        img_mask = threshA(img_t, threshLo = Lo , threshHi = Hi )
        img_mask = repairA(img_mask, iterations = 2)
        
        
        # LOCATE / TRACK
        x,y = find_xy(img_mask)
        radius = find_radius(img_mask)
        #print x, ' ', y, ' ', radius
        
        # if b_tracking_frame:
        #     x,y,radius = decrop_track(h_img, w_img)
        # b_track_success = filter_track()
        b_track_success = True


        #DRAW ONTO FRAME
        img_display = frame

        if b_tracking_frame:
            img_display = draw_tracking_frame(frame,x,y,radius)

        if b_drawTracking: # and b_track_success:
            img_display = draw_tracking(img_display,current_tracking_frame)

        b_annotate_img = False
        if b_annotate_img:
            img_display = draw_annotations(img_display, info_annotations)       
            

        # PROC & SHOW HISTOS
        if b_show_histos:
            
            if livehist == None:
                livehist = InitLiveHist(args["showbackghisto"])
                NUM_PLOTS = 6
                last_hist_update = time.time() - (hist_update_hz + 1)    #and process
            
            if time.time() - last_hist_update > hist_update_hz:

                # HISTO_PROCESSING
                if b_histo:
                    
                    rect_img = crop_img(frame.copy(), current_tracking_frame)
                    rect_list_px = px_to_list(rect_img)
                    hist_data_rect = px3clr_3px1clr(rect_list_px)
                    
                    backg_list_px = px_remove_crop(frame, current_tracking_frame)
                    hist_data_backg = px3clr_3px1clr(backg_list_px)
                
                    hist_data = hist_data_rect[:]
                    if args["showbackghisto"]:
                        hist_data.extend(hist_data_backg)

                # SHOW HISTOS
                if switch_new_ylim:
                    for hist_num in range(NUM_PLOTS):
                        
                        y_hist = np.histogram( hist_data[hist_num] )[0]
                        ymax = y_hist[1:].max()     #excluding bin0
                                    
                        livehist.set_ylim(y_lo = 0, y_hi = ymax * ylim_padding_mult
                                         ,ax_ind = (hist_num,) )
                        
                    switch_new_ylim = False

                livehist.update_figure( hist_data
                            ,ax_ind = range(NUM_PLOTS)
                            ,frames = 1
                            ,show = True
                            ,epsilon = .0001)
                
                last_hist_update = time.time()
 
        #SHOW IMAGES
        ret = showImages(img_display, b_show_main_img = True
                        ,b_show_transformed_img = True
                        ,img_t = img_t
                        ,b_show_mask_img = True
                        ,img_m = img_mask
                        )
        

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