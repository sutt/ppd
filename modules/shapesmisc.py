import os
import numpy as np
import cv2
import imutils
from matplotlib import image as mpimg
from matplotlib import pyplot as plt
import imgprocs
if False: from cv2 import *

''' almost DEPRECATED: only needed for shapes_seen() used once in iterThreshB '''

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
        img = imgprocs.transformA(img, blur= blur)
    
    mask = imgprocs.threshA(img, np.array(thresh[0], dtype = 'uint8'), 
                            np.array(thresh[1], dtype = 'uint8') )
    
    if repair_iters > 0:
        mask = imgprocs.repairA(mask,repair_iters)
    
    cnts = get_contours(mask)
    
    if b_ret_radius:
        return map(lambda c: get_enclosing_radius(c), cnts)
    if b_ret_area:
        return map(lambda c: cv2.contourArea(c), cnts)

    
