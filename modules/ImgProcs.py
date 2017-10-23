import os, sys, time, copy, random, argparse
import traceback
import numpy as np
import cv2
import imutils
from ImgUtils import px3clr_3px1clr
from ImgUtils import px_to_list
from matplotlib import image as mpimg
from matplotlib import pyplot as plt

def transformA(img, blur = 11, b_hsv = False):
    #frame = imutils.resize(frame, width=600)
    out = cv2.GaussianBlur(img, (blur, blur), 0)
    if b_hsv: return cv2.cvtColor(out, cv2.COLOR_BGR2HSV)
    return out    
    

def threshA(img, threshLo = (0,0,0), threshHi = (255,255,255)):
    return cv2.inRange(img, threshLo, threshHi)
    
def repairA(img, iterations = 2):
    img = cv2.erode(img, None, iterations=iterations)
    img = cv2.dilate(img, None, iterations=iterations)
    return img

def multi_thresh_cv(img1, img2, b_And = True, b_Or = False):
    return cv2.bitwise_and(img1,img2)
    

def multi_thresh(img1, img2, b_And = True, b_Or = False):
    
    ret = img1.copy()
    
    for r in range(0, len(img1)):
         for c in range(0,len(img1[0])):
            
            if b_And:
                if img2[r][c] == 0:
                    ret[r][c] = 0
            elif b_Or:
                if img2[r][c] == 1:
                    ret[r][c] = 1

    return ret


def px_data(img):
    return px3clr_3px1clr(px_to_list(img))

def px_range(data):
    return min(data), max(data)

def pct_inrange_cv(img, lo, hi, total = 0):
    t_mask = cv2.inRange(img, lo, hi )
    t_i = np.sum( t_mask  ) / 255
    if total == 0: total = len(img)*len(img[0])
    pct_i = float(t_i) / float(total)
    return pct_i



