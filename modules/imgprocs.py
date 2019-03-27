import os, sys, time, copy
import numpy as np
import cv2
import imutils
from imgutils import px3clr_3px1clr
from imgutils import px_to_list
from matplotlib import image as mpimg
from matplotlib import pyplot as plt
if False:
    from cv2 import *

''' image procedures used in color-thresholding protocols'''

def transformA(img, blur = 11, b_hsv = False):
    out = cv2.GaussianBlur(img, (blur, blur), 0)
    if b_hsv: return cv2.cvtColor(out, cv2.COLOR_BGR2HSV)
    return out    
    

def threshA(img, threshLo = (0,0,0), threshHi = (255,255,255)):
    return cv2.inRange(img, threshLo, threshHi)

def threshMultiOr(img, threshes = []):
    
    fullMask = np.array(np.zeros(shape = img.shape[:2]), dtype='bool')

    for _thresh in threshes:

        _mask = np.array(cv2.inRange(img, _thresh[0], _thresh[1]), dtype='bool')
                
        fullMask = np.bitwise_or(fullMask, _mask)
    
    return np.array(fullMask, dtype='uint8')
    
def repairA(img, iterations = 2):
    img = cv2.erode(img, None, iterations=iterations)
    img = cv2.dilate(img, None, iterations=iterations)
    return img

def px_range(data):
    return min(data), max(data)

def pct_inrange_cv(img, lo, hi, total = 0):
    t_mask = cv2.inRange(img, lo, hi )
    t_i = np.sum( t_mask  ) / 255
    if total == 0: total = len(img)*len(img[0])
    pct_i = float(t_i) / float(total)
    return pct_i


def find_xy(mask):
    
    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE)[-2]

    if len(cnts) > 0:
        c = max(cnts, key=cv2.contourArea)
        ((x, y), radius) = cv2.minEnclosingCircle(c)
        return (x,y)
    
    return 0,0

def find_radius(mask):

    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE)[-2]

    if len(cnts) > 0:
        c = max(cnts, key=cv2.contourArea)
        ((x, y), radius) = cv2.minEnclosingCircle(c)
        return radius
    return 0
