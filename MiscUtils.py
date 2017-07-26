import os, sys, time, copy, random, argparse, traceback
import numpy as np
import cv2
import imutils



def hist_from_img(inp_img):
    list_px = px_to_list(inp_img)
    on_pxs = px3clr_3px1clr(list_px)
    return on_pxs

def create_tracking_frame(**kwargs):
    return ((100,100),(300,300))

def mock_gaussian(n = 100, **kwargs ):
    z = np.random.randn(n)
    u, var = kwargs.get('u',0), kwargs.get('var',1)
    return map(lambda z_i: u + (z_i*var), z)
    
def rand_gauss_params():
    u = random.randint(0,255)
    var = random.randint(10,50)
    return u, var

def mock_hist_data():
    u, var = rand_gauss_params()
    hist_data = map( lambda x: mock_gaussian(n=100,u=u,var=var), range(3) )
    return hist_data