import numpy as np
import cv2
import sys, os, time, copy
import imutils
from GraphicsA import LiveHist
from ImgUtils import px3clr_3px1clr, px_to_list, px_remove_crop, crop_img


def InitLiveHist(b_include_backg = True, **kwargs):
    h, w = (2,3) if b_include_backg else (1,3)
    livehist = LiveHist( h = h, w = w, bins = kwargs.get('bins', 30)
                        ,x_lo = -1, x_hi = 256 ,y_lo = 0 ,y_hi = 7000 )
    livehist.show_plt(wait_time = 2)
    return livehist

def SwitchYLim(livehist, hist_data, exclude_zero = True ):
    #move this to GraphicsA
    for hist_num in range(livehist.N):
        y_hist = hist_data[hist_num][0]
        start_ind = 1 if exclude_zero else 0
        ymax = y_hist[start_ind:].max()     
                    
        livehist.set_ylim(y_lo = 0, y_hi = ymax, ax_ind = (hist_num,) )
                            

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

