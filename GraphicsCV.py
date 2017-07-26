import os, sys, time, copy, random, argparse
import traceback
import numpy as np
import cv2
import imutils
from collections import deque
from matplotlib import image as mpimg
from matplotlib import pyplot as plt



def draw_tracking_frame(img, x,y,radius):
    cv2.circle(img, (int(x), int(y)), int(radius), (0, 255, 255), 10)
    return img

def draw_tracking(img, rect ):
    cv2.rectangle(img, rect[0], rect[1], (0, 255, 255), 3)
    return img

def draw_annotations(img, info_annotations):
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img,'OpenCV',(10,10), font, 2,(255,255,255),2,cv2.LINE_AA)
    return img

def flip_img(img,flip = True):
    """return a non-copied image be default vertically flipped"""
    if flip:
        return cv2.flip(img,1)
    else:
        return img

def ShowImages(img_display,**kwargs):
    
    b_flip = not(kwargs.get('dont_mirror',False))

    if kwargs.get('b_show_main_img', False):
        cv2.imshow('display image'
                    ,flip_img(img_display, b_flip) )
    
    if kwargs.get('b_show_transformed_img', False):
        cv2.imshow('transformed image'
                    ,flip_img( kwargs.get('img_t',None), b_flip ) )

    if kwargs.get('b_show_mask_img', False):
        cv2.imshow('image mask'
                    ,flip_img( kwargs.get('img_m',None), b_flip ) )

    if kwargs.get('b_show_tracked_img', False):
        cv2.imshow('the ball',kwargs.get('on_pxs',None))
