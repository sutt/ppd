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
from modules.Methods import InitLiveHist, SwitchYLim, DelayFPS
from modules.GraphicsCV import draw_tracking_frame, draw_tracking, draw_annotations
from modules.GraphicsCV import ShowImages
from modules.ImgUtils import px3clr_3px1clr, px_to_list, px_remove_crop, crop_img
from modules.ImgProcs import threshA, transformA, repairA, multi_thresh_cv
from modules.TrackA import find_xy, find_radius
from modules.Methods import imgToPx, pxToHist, imgToPx2
from modules.Methods import Options
from modules.IterThresh import iterThreshA, iterThreshB, combine_threshes
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
ap.add_argument("--filecam", type=str, default="")
ap.add_argument("--fps_hz", type=str, default="30") #converted to int


args = vars(ap.parse_args())


def main():

    #INIT & PARAMS
    Globals.init()
    Globals.gui_pass1 = 0
    Globals.gui_cmd_quit = False
    Globals.gui_cmd_sw_agenda = False
    Globals.gui_cmd_reset_agenda = False
    Globals.gui_cmd_combine = False
    Globals.gui_cmd_set_rgb = False
    Globals.gui_cmd_set_hsv = False
    Globals.gui_cmd_expand = False
    Globals.gui_track_success = False
    Globals.gui_big_tracking_circle = False
    
    Globals.b_histo = args["showhisto"]     
    b_hist_rect = True
    Globals.b_show_histos = args["showhisto"]  
    b_histo_backg = args["showbackghisto"]
    switch_new_ylim = True  
    livehist = None
    hist_update_hz = 1
    
    b_tracking_frame = True
    b_drawTracking = True
    b_annotate_img = True
    Globals.b_show_puase_rect = False

    # TODO - one clean function here
    mid_xy = middle( (640,480), size = 80)[0][0]
    _tf = tf_gen(xy = mid_xy, square_size = 80)
    Globals.current_tracking_frame = (_tf[0],_tf[1]) #(xy,xy2)
    
    pause_rect = None       # TODO - deprecated? this is "4th display"
    Globals.threshLoHsv, Globals.threshHiHsv = (30,100,100), (100,200,200)
    Globals.threshLoRgb, Globals.threshHiRgb = (29, 86, 6), (64, 255, 255)
    Globals.b_thresh_hsv = False
    Globals.b_thresh_rgb = True

    Globals.thresh_pct = args["pctthresh"]  #0.95
    Globals.param_tracking_blur = 11
    Globals.param_tracking_repair_iters = 2
    b_thresh_log = True
    Globals.thresh_log = []

    log = Log()
    b_print_log = args["printlog"]  #TODO - move this to Log
    waitKeyRefresh = 1
    info_annotations = []
    b_slow_for_fps = True
    
    Globals.gui_camera_num = 0
    Globals.gui_camera_size_enum = 0

    b_gui = True
    if b_gui:
        gui = GuiA()

    #OUTER LOOP - to reset camera
    while(not(Globals.gui_cmd_quit)):

        Globals.gui_camera_reset = False

        cam_params = [(640,480),(1280,720),(1920,1080)][Globals.gui_camera_size_enum]
        
        h_img, w_img = cam_params[0], cam_params[1]
        cam_type = 'cv_cam'   # 'pi_cam','file_cam'

        b_agenda = args["agenda"]
        Globals.sw_agenda = False
        if b_agenda: 
            agenda = AgendaA(img_wh = cam_params)
            agenda.do_rect_move()

        vc = initCam(cam_type, vid_file = args["filecam"]
                     ,usb_num = Globals.gui_camera_num ) 

        if args["filecam"] == "":
            vc = setupCam(vc, cam_type = cam_type, params = cam_params)
        
        time_last = time.time()
        i = 0

        while(vc.isOpened()):

            ret, frame = getFrame(vc, cam_type = 'cv_cam')        
            i += 1
            if not(ret): break

            if i == 1: print frame.shape

            # THRESHOLD MASK    
            img_mask_hsv, img_mask_rgb = None, None
            if Globals.b_thresh_hsv:
                img_t = transformA(frame.copy(), b_hsv = True, blur = Globals.param_tracking_blur)
                img_mask_hsv = threshA(img_t 
                                    ,threshLo = Globals.threshLoHsv 
                                    ,threshHi = Globals.threshHiHsv )
            
            if Globals.b_thresh_rgb:
                img_t = transformA(frame.copy(), Globals.param_tracking_blur)
                img_mask_rgb = threshA(img_t 
                                    ,threshLo = Globals.threshLoRgb 
                                    ,threshHi = Globals.threshHiRgb )
            
            #TODO - make this a function
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
            
            b_track_success = False

            if not(img_mask is None):
                b_mask_img = True
                img_mask = repairA(img_mask, iterations = Globals.param_tracking_repair_iters)
            
                # LOCATE / TRACK
                x,y = find_xy(img_mask)
                radius = find_radius(img_mask)
                
                if radius > 0:
                    b_track_success = True
            else:
                b_mask_img = False


            #DRAW ONTO FRAME

            img_t = transformA(frame.copy(), b_hsv = Globals.b_thresh_hsv
                        ,blur = Globals.param_tracking_blur)

            if Globals.gui_track_success:
                info_annotations.append(b_track_success)
                b_annotate_img = True
            else:
                b_annotate_img = False
            
            img_display = frame.copy()

            if b_tracking_frame:
                img_display = draw_tracking_frame(img_display,x,y,radius)

            if b_drawTracking:
                img_display = draw_tracking(img_display,Globals.current_tracking_frame)

            if b_annotate_img:
                img_display = draw_annotations(img_display, info_annotations)       
                
            if Globals.gui_big_tracking_circle and b_track_success:
                img_mask = draw_tracking_frame(img_mask,x,y,radius + 10, one_color = True)  

            #SHOW IMAGES
            dont_mirror = True if Globals.gui_camera_num == 1 else False

            ShowImages(  display_img = True,   img_d = img_display
                        ,transform_img = True, img_t = img_t
                        ,mask_img = b_mask_img,      img_m = img_mask 
                        ,pause_rect = Globals.b_show_puase_rect
                        ,img_rect = pause_rect
                        ,resize = True
                        ,dont_mirror = dont_mirror)
            

            # AGENDA
            if b_agenda:
                
                if Globals.gui_cmd_reset_agenda:
                    Globals.gui_cmd_reset_agenda = False
                    agenda = AgendaA(img_wh = cam_params)
                    agenda.do_rect_move()
            
                # agenda.timer()
                        
                if Globals.sw_agenda:
                    
                    Globals.sw_agenda = False
                    img_crop = crop_img(frame.copy(), Globals.current_tracking_frame)
                    agenda.log_rect_imgs(img_crop)
                    agenda.write_rect_files(img_crop)
                    agenda.do_rect_move()
                    
                if Globals.gui_cmd_combine:
                    Globals.gui_cmd_combine = False
                    agenda.run_combine()
                    if b_gui:
                        temp_thresh = agenda.get_temp_threshes()
                        gui.globeGui.set_gui_to_output(temp_thresh)

                if Globals.gui_cmd_expand:
                    Globals.gui_cmd_expand = False
                    agenda.log_backg_img(img = frame.copy())
                    agenda.write_backg_files(img = frame.copy())
                    print 'expansssssssionn to: ', str(Globals.max_width_to_expand)
                    agenda.run_expand()
                    if b_gui:
                        temp_thresh = agenda.get_temp_threshes()
                        gui.globeGui.set_gui_to_output(temp_thresh)

                if Globals.gui_cmd_set_rgb:
                    Globals.gui_cmd_set_rgb = False
                    agenda.apply_thresh_from_temp('rgb')
                    gui.globeGui.set_gui_to_thresh(typ = 'rgb')

                if Globals.gui_cmd_set_hsv:
                    Globals.gui_cmd_set_hsv = False
                    agenda.apply_thresh_from_temp('hsv')
                    gui.globeGui.set_gui_to_thresh(typ = 'hsv')

            
            if cam_type == 'file_cam' and b_slow_for_fps:
                DelayFPS(time_last, int(args["fps_hz"]))
                time_last = time.time()

            # LOGGING
            if b_print_log:
                print 'frame time: %.2f' % (time.time() - time_last)
                print 'b_show_histos: ', str(Globals.b_show_histos)
                time_last = time.time()

            if cv2.waitKey(waitKeyRefresh)== ord('q'):
                break

            if Globals.gui_cmd_quit:
                break

            if Globals.gui_camera_reset:
                break
            
            # DEBUGGING
            #print str(Globals.threshLoRgb), ' ', str(Globals.threshHiRgb)
            #print str(Globals.threshLoHsv), ' ', str(Globals.threshHiHsv)
            # print 'RGB-b: ', str(Globals.b_thresh_rgb)
            # print 'HSV-b: ', str(Globals.b_thresh_hsv)
            # print Globals.thresh_pct
        
        #CLEANUP
        vc.release()
        cv2.destroyAllWindows()
        #if args['writebookvideo']: vw.release()


main()