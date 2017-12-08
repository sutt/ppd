import os, sys, time, copy, random, argparse, traceback
import numpy as np
import cv2
import imutils


def initCam(cam_type,**kwargs):
    if cam_type == 'cv_cam': 
            return cv2.VideoCapture(kwargs.get('usb_num',0) )
    elif cam_type == 'pi_cam': 
        return 1
    elif cam_type == 'file_cam': 
        return  cv2.VideoCapture(kwargs.get('vid_file'))
    else:
        print 'No cam object creatable.'

def setupCam(vc, cam_type, params):
    # set ISO, shutter speed, fps, etc...
    try:
        if params[0] == 640:
            vc.set(3,640)
            vc.set(4,480)
        elif params[0] == 1280:
            vc.set(3,1280)
            vc.set(4,720)
        elif params[0] == 1920:
            vc.set(3,1920)
            vc.set(4,1080)
        
    except Exception as e:
        print 'Could not set cam params: ', str(e)
        print traceback.format_exc()
    return vc

def getFrame(inp_cam, cam_type):
        if cam_type == 'cv_cam': 
            return inp_cam.read()
        elif cam_type == 'pi_cam': 
            return True, inp_cam
        elif cam_type == 'file_cam': 
            return inp_cam.read()
        else:
            print 'No frame read possible.'
