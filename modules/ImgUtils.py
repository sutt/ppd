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
    if (img.shape) == 3:
        return img[y0:y1,x0:x1,:]    
    else:
        return img[y0:y1,x0:x1]    

def circle_xcoords(radius):
    ''' returns list of length radius, with each x coord on the unit circle line'''    
    list_x = []
    for y in range(1, radius + 1):
        list_x.append( (radius**2 - y**2)**(0.5) )
    return list_x

def filter_pixels_circle(img, b_inside=True):
    
    pix_list = []
    
    #make circle based on img-shape:
    circle_x = int( img.shape[1] / 2)
    circle_y = int( img.shape[0] / 2)
    radius = min( int(img.shape[1] / 2), int(img.shape[0] / 2) )    
    
    #build the x_coords frontier contour
    x_coords = map(int, circle_xcoords(radius)[::-1])
    x_coords.extend(x_coords[::-1])
    
    #filter loop
    for y in range(img.shape[0]):
        for x in range(img.shape[1]):
            
            if (y <= circle_y - radius) or (y >= circle_y + radius):
                if not(b_inside):
                    pix_list.append(img[y,x])
                else:
                    continue
            
            _y = y - (circle_y - radius) 
                
            if (x > circle_x - x_coords[_y]) and (x < circle_x + x_coords[_y]):
                if b_inside:
                    pix_list.append(img[y,x])
            else:
                if not(b_inside):
                    pix_list.append(img[y,x])
    
    return pix_list

def pixlist_to_pseduoimg(pix_list):
    return np.array(pix_list, dtype='uint8', ndmin = 3)
    #flatten? ndmin (sic?) pseduo (sic?)

def binary_diff(inputDiff):
    ''' return a diff as an binary (0 or 255) for each pixel'''

    imgDiff = cv2.cvtColor(inputDiff, cv2.COLOR_BGR2GRAY)

    h, w = imgDiff.shape
    binaryDiff = np.zeros(shape =(h,w,3))

    for x in range(w-1):
        for y in range(h-1):
            
            #TODO - allow single channel output as well
            # binaryDiff[y,x] = 0 if (imgDiff[y,x] == 0) else 255
            
            binaryDiff[y,x] = (
                        np.array([0,0,0], dtype = np.uint8) 
                        if (imgDiff[y,x] == 0) else  
                        np.array([255,255,255], dtype = np.uint8)
            )

    return binaryDiff