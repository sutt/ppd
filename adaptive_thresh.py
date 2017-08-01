import os, sys, time, copy, random, argparse
import traceback
import numpy as np
import cv2
import imutils
from collections import deque
from matplotlib import image as mpimg
from matplotlib import pyplot as plt

import Globals
from Camera import initCam, setupCam, getFrame
from GraphicsA import LiveHist
from AppUtils import write_pic, uni_dir, make_dir
from Methods import InitLiveHist, SwitchYLim
from GraphicsCV import draw_tracking_frame, draw_tracking, draw_annotations
from GraphicsCV import ShowImages
from ImgUtils import px3clr_3px1clr, px_to_list, px_remove_crop, crop_img
from ImgProcs import threshA, transformA, repairA
from TrackA import find_xy, find_radius
from Methods import imgToPx, pxToHist, imgToPx2
from Methods import Options
#from MiscUtils import hist_from_img, create_tracking_frame
#from MiscUtils import mock_gaussian, rand_gauss_params, mock_hist_data

ap = argparse.ArgumentParser()
ap.add_argument("--file", type=str, default="fps30.h264")
ap.add_argument("--showhisto", action="store_true")
ap.add_argument("--showbackghisto", action="store_true")
ap.add_argument("--startuppause", action="store_true")
ap.add_argument("--printlog", action="store_true")
args = vars(ap.parse_args())


def main():

    #INIT & PARAMS
    Globals.init()
    
    b_tracking_frame = True
    Globals.b_histo = args["showhisto"]     
    b_hist_rect = True
    Globals.b_show_histos = args["showhisto"]  
    b_histo_backg = args["showbackghisto"]
    b_drawTracking = True
    b_print_log = args["printlog"]
    Globals.b_show_puase_rect = False

    hist_update_hz = 1
    waitKeyRefresh = 1
    current_tracking_frame = ((100,100),(200,200))
    pause_rect = None
    Globals.threshLo, Globals.threshHi = (29, 86, 6), (64, 255, 255)

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
        img_mask = threshA(img_t 
                            ,threshLo = Globals.threshLo 
                            ,threshHi = Globals.threshHi )
        img_mask = repairA(img_mask, iterations = 2)
        
        # LOCATE / TRACK
        x,y = find_xy(img_mask)
        radius = find_radius(img_mask)
        
        # FILTER TRACK
        b_track_success = True

        #DRAW ONTO FRAME
        img_display = frame.copy()

        if b_tracking_frame:
            img_display = draw_tracking_frame(img_display,x,y,radius)

        if b_drawTracking:
            img_display = draw_tracking(img_display,current_tracking_frame)

        b_annotate_img = False
        if b_annotate_img:
            img_display = draw_annotations(img_display, info_annotations)       
            

        # PROC & SHOW HISTOS
        if Globals.b_show_histos:
            
            if livehist == None:
                livehist = InitLiveHist(b_histo_backg
                                       ,b_pause = args["startuppause"])
                last_hist_update = time.time() - (hist_update_hz + 1)    #and process
            
            if time.time() - last_hist_update > hist_update_hz:

                if Globals.b_histo:
                    px_data = imgToPx(img_t, current_tracking_frame, ) ##frame should be img
                    if Globals.b_show_puase_rect: 
                        px_data = imgToPx2(img_t, pause_rect, current_tracking_frame )
                    hist_data = pxToHist(px_data)
                    # print '---------' 
                    # print hist_data[0][0]
                    # print '---------'
                
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
                    ,mask_img = True,      img_m = img_mask 
                    ,pause_rect = Globals.b_show_puase_rect
                    ,img_rect = pause_rect
                    ,resize = True)
        

        if cv2.waitKey(waitKeyRefresh)== ord('q'):
            print 'quitting cv loop'
            break
        if cv2.waitKey(waitKeyRefresh)== ord('p'):
            print 'taking picture of rect'
            pause_rect = crop_img(img_t.copy(), current_tracking_frame)
            Globals.b_show_puase_rect = True
        
        if cv2.waitKey(waitKeyRefresh)== ord('l'):
            
            writepath = "data/write/july"
            output_dir = uni_dir(writepath)
            make_dir(writepath + "/" + output_dir)
            print 'writing out to: ', output_dir
            
            write_pic(frame
                     ,name_base="img",path=output_dir)
            write_pic(img_t
                     ,name_base="img_t",path=output_dir)
            write_pic(crop_img(frame.copy(), current_tracking_frame)
                     ,name_base="rect",path=output_dir)
            write_pic(crop_img(img_t.copy(), current_tracking_frame)
                     ,name_base="rect_t",path=output_dir)
            

        if cv2.waitKey(waitKeyRefresh) == ord('o'):
            while(True):
                ret = Options()
                if ret == 1: 
                    break

        # if cam_type == 'file_cam' and b_slow_for_fps:
            # DelayFPS(time_last, 30)

        # LOGGING
        if b_print_log:
            print 'frame time: %.2f' % (time.time() - time_last)
            print 'b_show_histos: ', str(Globals.b_show_histos)
            time_last = time.time()

    #CLEANUP
    vc.release()
    cv2.destroyAllWindows()
    #if args['writebookvideo']: vw.release()


main()