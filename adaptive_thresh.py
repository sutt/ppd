import os, sys, time, copy, random, argparse
import traceback
import numpy as np
import cv2
import imutils
from collections import deque
from matplotlib import image as mpimg
from matplotlib import pyplot as plt
import Tkinter as tk
import threading

import modules.Globals as Globals
from modules.Camera import initCam, setupCam, getFrame
from modules.GraphicsA import LiveHist
from modules.AppUtils import write_pic, uni_dir, make_dir
from modules.Methods import InitLiveHist, SwitchYLim
from modules.GraphicsCV import draw_tracking_frame, draw_tracking, draw_annotations
from modules.GraphicsCV import ShowImages
from modules.ImgUtils import px3clr_3px1clr, px_to_list, px_remove_crop, crop_img
from modules.ImgProcs import threshA, transformA, repairA, multi_thresh_cv
from modules.TrackA import find_xy, find_radius
from modules.Methods import imgToPx, pxToHist, imgToPx2
from modules.Methods import Options
from modules.IterThresh import iterThreshA, combine_threshes
from modules.Agenda import AgendaA
from modules.Agenda import middle, corners, tf_gen
from modules.GuiA import GuiA
from modules.LoggingA import Log

ap = argparse.ArgumentParser()
ap.add_argument("--file", type=str, default="fps30.h264")
ap.add_argument("--showhisto", action="store_true")
ap.add_argument("--showbackghisto", action="store_true")
ap.add_argument("--startuppause", action="store_true")
ap.add_argument("--printlog", action="store_true")
ap.add_argument("--agenda", action="store_true")
ap.add_argument("--agendatimer", action="store_true")
ap.add_argument("--pctthresh", type=float, default=0.95)

args = vars(ap.parse_args())


def main():

    #INIT & PARAMS
    Globals.init()
    Globals.gui_pass1 = 0
    Globals.gui_cmd_quit = False
    Globals.gui_cmd_sw_agenda = False
    Globals.b_histo = args["showhisto"]     
    b_hist_rect = True
    Globals.b_show_histos = args["showhisto"]  
    b_histo_backg = args["showbackghisto"]
    switch_new_ylim = True  
    livehist = None
    
    b_tracking_frame = True
    b_drawTracking = True
    b_annotate_img = True
    Globals.b_show_puase_rect = False

    mid_xy = middle( (640,480), size = 80)[0][0]
    _tf = tf_gen(xy = mid_xy, square_size = 80)
    Globals.current_tracking_frame = (_tf[0],_tf[1]) #(xy,xy2)
    
    pause_rect = None
    Globals.threshLoHsv, Globals.threshHiHsv = (30,100,100), (100,200,200)
    Globals.threshLoRgb, Globals.threshHiRgb = (29, 86, 6), (64, 255, 255)
    Globals.b_thresh_hsv = False
    Globals.b_thresh_rgb = True

    Globals.thresh_pct = args["pctthresh"]  #0.95
    b_thresh_log = True
    Globals.thresh_log = []

    log = Log()
    b_print_log = args["printlog"]
    hist_update_hz = 1
    waitKeyRefresh = 1
    time_last = time.time()
    info_annotations = []
    i = 0
    
    cam_params = (640,480)
    h_img, w_img = cam_params[0], cam_params[1]
    cam_type = 'cv_cam'   # 'pi_cam','file_cam'

    b_agenda = args["agenda"]
    sw_agenda = False
    if b_agenda: 
        agenda = AgendaA(img_wh = cam_params
                        ,b_hsv_thresh = True
                        ,b_rgb_thresh = True)
        b_agenda_timer = args["agendatimer"]
        sw_reset_agenda_timer = False
        next_agenda_time = time.time() + 999999.9


    vc = initCam(cam_type)
    vc = setupCam(vc, cam_type = cam_type, params = cam_params)

    gui = GuiA()

    while(vc.isOpened()):

        ret, frame = getFrame(vc, cam_type = 'cv_cam')        
        i += 1
        if not(ret): break

        # THRESHOLD MASK    
        img_mask_hsv, img_mask_rgb = None, None
        if Globals.b_thresh_hsv:
            img_t = transformA(frame.copy(), b_hsv = True)
            img_mask_hsv = threshA(img_t 
                                ,threshLo = Globals.threshLoHsv 
                                ,threshHi = Globals.threshHiHsv )
        
        if Globals.b_thresh_rgb:
            img_t = transformA(frame.copy())
            img_mask_rgb = threshA(img_t 
                                ,threshLo = Globals.threshLoRgb 
                                ,threshHi = Globals.threshHiRgb )

        if True: #Globals.b_thresh_hsv:
            img_t = transformA(frame.copy(), b_hsv = True)
        
        img_mask = None
        if Globals.b_thresh_hsv and  Globals.b_thresh_rgb:
            if not(img_mask_hsv is None) and not(img_mask_rgb is None):
                img_mask = multi_thresh_cv(img_mask_hsv,img_mask_rgb)
        elif Globals.b_thresh_hsv:
            img_mask = img_mask_hsv
        elif Globals.b_thresh_rgb:
            img_mask = img_mask_rgb
        else:
            log.log("MSG_NO_THRESHES")
        
        if not(img_mask is None):
            b_mask_img = True
            img_mask = repairA(img_mask, iterations = 2)
        
            # LOCATE / TRACK
            x,y = find_xy(img_mask)
            radius = find_radius(img_mask)
            b_track_success = True
        else:
            b_mask_img = False

        #DRAW ONTO FRAME
        img_display = frame.copy()

        if b_tracking_frame:
            img_display = draw_tracking_frame(img_display,x,y,radius)

        if b_drawTracking:
            img_display = draw_tracking(img_display,Globals.current_tracking_frame)

        if b_annotate_img:
            img_display = draw_annotations(img_display, info_annotations)       
            


        #SHOW IMAGES
        ShowImages(  display_img = True,   img_d = img_display
                    ,transform_img = True, img_t = img_t
                    ,mask_img = b_mask_img,      img_m = img_mask 
                    ,pause_rect = Globals.b_show_puase_rect
                    ,img_rect = pause_rect
                    ,resize = True)
        

        if cv2.waitKey(waitKeyRefresh)== ord('q'):
            print 'quitting cv loop'
            break
        
        # if cam_type == 'file_cam' and b_slow_for_fps:
            # DelayFPS(time_last, 30)

        
        # AGENDA
        if b_agenda:
        
            if b_agenda_timer:
                if (sw_agenda == False) and sw_reset_agenda_timer:
                    next_agenda_time = time.time() + 3.0
                    sw_reset_agenda_timer = False

                elif time.time() > next_agenda_time:
                    sw_agenda = True

                else:
                    _temp = round(next_agenda_time - time.time(), 1)
                    if _temp < 10: _temp = "*" * int(_temp * 2)
                    info_annotations.append(_temp)
                    
            if sw_agenda:
                #bug do a blur
                img_crop = crop_img(frame.copy(), Globals.current_tracking_frame)
                
                agenda.log_rect_imgs(img_crop)
                agenda.write_rect_files(img_crop)
                agenda.do_rect_move()
                
                if (agenda.seq_end) and not(agenda.sw_calcd_combined):
                    
                    if agenda.b_rgb_thresh:
                        print 'setting rgb'
                        _lo, _hi = agenda.combine_threshes()
                        agenda.print_logs()
                        agenda.apply_thresh(_lo,_hi)

                    if agenda.b_hsv_thresh:
                        _lo, _hi = agenda.combine_threshes(thresh_type = 'hsv')
                        agenda.print_logs()
                        print 'setting hsv'
                        agenda.apply_thresh(_lo,_hi, thresh_type = 'hsv')

                sw_agenda = False
                if b_agenda_timer: sw_reset_agenda_timer = True


        # LOGGING
        if b_print_log:
            print 'frame time: %.2f' % (time.time() - time_last)
            print 'b_show_histos: ', str(Globals.b_show_histos)
            time_last = time.time()

        
        #GUI GLOBALS GET/SET
        if Globals.gui_cmd_sw_agenda:
            sw_agenda = True
            Globals.gui_cmd_sw_agenda = False

        if Globals.gui_cmd_quit:
            break
        
        # DEBUGGING
        #print str(Globals.threshLoRgb), ' ', str(Globals.threshHiRgb)
        #print str(Globals.threshLoHsv), ' ', str(Globals.threshHiHsv)
        # print 'RGB-b: ', str(Globals.b_thresh_rgb)
        # print 'HSV-b: ', str(Globals.b_thresh_hsv)
    
    #CLEANUP
    vc.release()
    cv2.destroyAllWindows()
    #if args['writebookvideo']: vw.release()


main()