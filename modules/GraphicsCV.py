import os, sys, time, copy, random, argparse
import traceback
import numpy as np
import cv2
import imutils
from collections import deque
from matplotlib import image as mpimg
from matplotlib import pyplot as plt



def draw_tracking_frame(img, x,y,radius, **kwargs):
    if kwargs.get('one_color',False):
        cv2.circle(img, (int(x), int(y)), int(radius), (255), 10)
    else:
        cv2.circle(img, (int(x), int(y)), int(radius), (0, 255, 255), 10)
    return img

def draw_tracking(img, rect ):
    cv2.rectangle(img, rect[0], rect[1], (0, 255, 255), 3)
    return img

def draw_annotations(img, info_annotations):
    if len(info_annotations) == 0: return img
    try:
        disp_text = str(info_annotations.pop())
    except:
        disp_text = 'err'
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img,disp_text,(50,50), font, 2,(255,255,255),2,cv2.LINE_AA)
    return img

def flip_img(img,flip = True):
    """return a non-copied image be default vertically flipped"""
    if flip:
        return cv2.flip(img,1)
    else:
        return img

def resize_img(img, resize, resize_dims = (640,480)):
    """return a non-copied image resized"""
    if resize:
        return imutils.resize(img
                             ,width = resize_dims[0]
                             ,height =resize_dims[1] )
    else:
        return img

def ShowImages(**kwargs):
    
    b_flip = not(kwargs.get('dont_mirror',False))
    b_resize = kwargs.get('resize',False)

    if kwargs.get('display_img', False):
        img = resize_img(kwargs.get('img_d',None), b_resize, (640,480) )
        img = flip_img(img, b_flip)
        cv2.imshow('display image', img )
    
    if kwargs.get('transform_img', False):
        img = flip_img( kwargs.get('img_t',None), b_flip )
        img = resize_img(img, b_resize, (320,240) )
        cv2.imshow('transform image', img)
                    

    if kwargs.get('mask_img', False):
        img = flip_img( kwargs.get('img_m',None), b_flip )
        img = resize_img(img, b_resize, (320,240) )
        cv2.imshow('mask image', img)
                    

    if kwargs.get('tracked_img', False):
        cv2.imshow('the ball',kwargs.get('on_pxs',None))

    if kwargs.get('pause_rect', False):
        img = flip_img( kwargs.get('img_rect',None), b_flip )
        cv2.imshow('pause_rect', img)
