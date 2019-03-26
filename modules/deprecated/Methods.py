import numpy as np
import cv2
import sys, os, time, copy
import imutils
from GraphicsA import LiveHist
from ImgUtils import px3clr_3px1clr, px_to_list, px_remove_crop, crop_img
import Globals
#from adaptive_thresh import b_show_histos, b_histo, current_tracking_frame

def InitLiveHist(b_include_backg = True, **kwargs):
    h, w = (2,3) if b_include_backg else (1,3)
    livehist = LiveHist( h = h, w = w, bins = kwargs.get('bins', 30)
                        ,x_lo = -1, x_hi = 256 ,y_lo = 0 ,y_hi = 7000 )
    wt = 2 if kwargs.get('b_pause',False) else 0.01
    livehist.show_plt(wait_time = wt)

    return livehist

def SwitchYLim(livehist, hist_data, exclude_zero = True ):
    #move this to GraphicsA
    for hist_num in range(livehist.N):
        y_hist = hist_data[hist_num][0]
        start_ind = 1 if exclude_zero else 0
        ymax = y_hist[start_ind:].max()     
                    
        livehist.set_ylim(y_lo = 0, y_hi = ymax, ax_ind = (hist_num,) )
                            
def imgToPx2(img, pause_img, rect, include_backg = True):
    """returns list of list of px's for each color, for both rect and backg"""
    rect_img = pause_img.copy()
    rect_list_px = px_to_list(rect_img)
    px_data_rect = px3clr_3px1clr(rect_list_px)
    
    backg_list_px = px_remove_crop(img, rect)
    px_data_backg = px3clr_3px1clr(backg_list_px)

    px_data = px_data_rect[:]
    if include_backg:
        px_data.extend(px_data_backg)
    return px_data


def imgToPx(img, rect, include_backg = True):
    """returns list of list of px's for each color, for both rect and backg"""
    rect_img = crop_img(img.copy(), rect)
    rect_list_px = px_to_list(rect_img)
    px_data_rect = px3clr_3px1clr(rect_list_px)
    
    backg_list_px = px_remove_crop(img, rect)
    px_data_backg = px3clr_3px1clr(backg_list_px)

    px_data = px_data_rect[:]
    if include_backg:
        px_data.extend(px_data_backg)
    return px_data

def pxToHist(px_data, **kwargs):
    """ return list of (n, bins) from list of px_array's """
    return map(lambda px_array: np.histogram(px_array,30), px_data)

def Options(**kwargs):

    ret = raw_input('options ... show_histo, hide_histo, new_tracking_frame x0 y0 x1 y1, quit \n>')                

    if ret == 'quit':
        print 'quitting options...'
        return 1

    elif ret[:10] == "show_histo":
        Globals.b_show_histos = True
        Globals.b_histo = True
    
    elif ret[:10] == "hide_histo":
        Globals.b_show_histos = False
        Globals.b_histo = False
        print 'print changing: ', Globals.b_histo

    elif ret[:12] == "unpause_rect":
        Globals.b_show_pause_rect = False
        print 'allowing rect histos to change again'

    elif ret[:18] == "new_tracking_frame":
        
        opt_args = ret.split(' ')
        if len(opt_args) > 1:
            try:
                x0,y0,x1,y1 = int(opt_args[1]), int(opt_args[2]),  int(opt_args[3]), int(opt_args[4])
                Globals.current_tracking_frame = ((x0,y0),(x1,y1))
                print 'changing tracking_frame to: ', str(Globals.current_tracking_frame)
                switch_new_ylim = True
                print 'switching rect hist ylim'
            except:
                print 'could not set tracking_frame.'    
        else:
            print 'did not recognize length of tracking_frame input.'
    
    elif ret[:14] == "current_thresh":
        print 'HSV thresh: ', str(Globals.b_thresh_hsv)
        print 'Lo: ', str(Globals.threshLoHsv), ' Hi: ', str(Globals.threshHiHsv)
        print 'RGB thresh: ', str(Globals.b_thresh_rgb)
        print 'Lo: ', str(Globals.threshLoRgb), ' Hi: ', str(Globals.threshHiRgb)

    elif ret[:10] == "set_thresh":
        
        opt_args = ret.split(' ')
        if len(opt_args) > 1:
            thresh_type = "hsv" if opt_args[1][:1] == "h" else "rgb"
            print 'thresh type: %s' % thresh_type
            pre = 1
            try:
                b0,g0,r0 = int(opt_args[pre+1]), int(opt_args[pre+2]),  int(opt_args[pre+3])
                b1,g1,r1 = int(opt_args[pre+4]), int(opt_args[pre+5]),  int(opt_args[pre+6])
                if thresh_type == "hsv":
                    Globals.threshLoHsv = (b0,g0,r0)
                    Globals.threshHiHsv = (b1,g1,r1)
                else:
                    Globals.threshLoRgb = (b0,g0,r0)
                    Globals.threshHiRgb = (b1,g1,r1)
                print 'switching thresh %s to: ' % str(thresh_type)
                print str(Globals.threshLoHsv), ' ', str(Globals.threshHiHsv)
                
                Globals.b_show_puase_rect = False
                print 'and turning off b_show_pause_rect'

            except:
                print 'could not set thresh'    
        else:
            print 'did not recognize length of set_thresh'

    elif ret[:15] == "set_type_thresh":
        
        opt_args = ret.split(' ')
        if len(opt_args) == 3:
             
            if str(opt_args[2]) == "True": thresh_bool = True
            elif str(opt_args[2]) == "False": thresh_bool = False
            else:
                print 'no truth value in arguments'
            
            if str(opt_args[1]) == "hsv": thresh_type = 'hsv'
            elif str(opt_args[1]) == "rgb": thresh_type = 'rgb'
            else:
                print 'no recognize thresh type in arguments'

            if thresh_type == 'hsv':
                Globals.b_thresh_hsv = thresh_bool
            if thresh_type == 'rgb':
                Globals.b_thresh_rgb = thresh_bool
        
            print 'changing thresh ' , str(thresh_type), ' to: ', str(thresh_bool)

        else:
            print 'not correct amount of arguments, try: set_thresh_type hsv True'

    else:
        print 'option <', str(ret),'> not recognized'

    return 0

    

def DelayFPS(time_last_frame, fps_hz):
    fps_time = 1.0/float(fps_hz)
    current_frames_time = time.time() - time_last_frame 
    sleep_time = fps_time - current_frames_time
    if sleep_time > 0:
        time.sleep(sleep_time)
    return 0
    

