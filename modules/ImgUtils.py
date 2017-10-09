import os, sys, time, copy, random, argparse
import traceback
import numpy as np
import cv2
import imutils
from matplotlib import image as mpimg
from matplotlib import pyplot as plt



def px3clr_3px1clr(list_pixels):
    return [ map( lambda v: v[clr], list_pixels ) for clr in range(3)]

def px_to_list(img):
    hL,wL = img.shape[0], img.shape[1]  
    return [ tuple( img[h,w,:] ) for h in range(hL) for w in range(wL) ]
            
def px_remove_crop(img, crop_params ):
    x0,y0 = crop_params[0]
    x1,y1 = crop_params[1]
    hL,wL,cL = img.shape
    return [ tuple( img[h,w,:] ) for h in range(hL) for w in range(wL) 
                if ((h < y0) or (h > y1)) and
                   ((w < x0) or (w > x1)) ]

def crop_img(img, current_tracking_frame):
    x0,y0 = current_tracking_frame[0][0], current_tracking_frame[0][1]
    x1,y1 = current_tracking_frame[1][0], current_tracking_frame[1][1]
    return img[x0:x1,y0:y1,:]    