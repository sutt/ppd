import os
import numpy as np
import cv2
import imutils
from collections import deque
from matplotlib import image as mpimg
from matplotlib import pyplot as plt
import ImgProcs


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

def get_contours(inp):
    return cv2.findContours(inp.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]

def top_contour(cnts):
    if len(cnts) > 0:
        c = max(cnts, key=cv2.contourArea)
        return c

def bottom_contour(cnts):
    if len(cnts) > 0:
        c = min(cnts, key=cv2.contourArea)
        return c

def get_enclosing_radius(c):
    ((x, y), radius) = cv2.minEnclosingCircle(c)
    return radius

def shapes_seen(img, thresh, blur = 11, repair_iters = 0, b_ret_radius = True, b_ret_area = False):
    
    if blur > 0:
        img = ImgProcs.transformA(img, blur= blur)
    
    mask = ImgProcs.threshA(img, np.array(thresh[0], dtype = 'uint8'), 
                            np.array(thresh[1], dtype = 'uint8') )
    
    if repair_iters > 0:
        mask = ImgProcs.repairA(mask,repair_iters)
    
    cnts = get_contours(mask)
    
    if b_ret_radius:
        return map(lambda c: get_enclosing_radius(c), cnts)
    if b_ret_area:
        return map(lambda c: cv2.contourArea(c), cnts)

if __name__ == "__main__":
    
    img_p  = "C:/Users/wsutt/Desktop/files/ppd/ppd/data/write/july/imgs21/img1.jpg"
    img = cv2.imread(img_p)
    lo,hi = [5, 2, 6], [43, 32, 34]
    thresh1 = (np.array( lo , dtype = 'uint8' ), np.array( hi , dtype = 'uint8' ))
    out = shapes_seen(img,thresh = thresh1 )
    print out
    print "\n"
    out = shapes_seen(img,thresh = thresh1, repair_iters = 7 )
    print out