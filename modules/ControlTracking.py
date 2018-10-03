import os, sys, time, copy, json, re, argparse

import numpy as np
import cv2

sys.path.append("../")
from vidwriter import VidWriter
from miscutils import uniqueFn

from modules.Utils import TimeLog
from modules.Utils import MetaDataLog

from modules.ImgProcs import threshA, transformA, repairA
from modules.TrackA import find_xy, find_radius

# from modules import GlobalsC as g

class TrackFactory:

    ''' handles tracking processing and tracking-stored-data '''
    
    def __init__(self, on=False):
        self.on = on
        self.currentFrame = None
        
        self.currentTrackSuccess = False
        self.currentTrackRoi = None
        self.currentTrackCircle = None

        self.threshInitial = ( (0,0,0), (255,255,255) )

        self.declaredBallColor = ""

        # TrackingAlgo class inherits TrackingTemplate 
        # and is instantiated here?

    def setInit(self, ballColor = ""):
        self.declaredBallColor = ballColor
        
        if self.declaredBallColor == "green":
            self.threshInitial = ( (29, 86, 6), (64, 255, 255) )
    
    def getCurrentTrackRoi(self):
        if not(self.on): return None
        return self.currentTrackRoi

    def getCurrentTrackCircle(self):
        if not(self.on): return None
        return self.currentTrackCircle

    def setFrame(self, currentFrame):
        if not(self.on): return
        self.currentFrame = currentFrame

    def trackFrame(self):

        if not(self.on): return

        tracking_blur = 1       # needs to be even or odd?
        repair_iterations = 1 

        thresh_lo = (0,0,0)
        thresh_hi = (255,255,255)

        thresh_lo = self.threshInitial[0]
        thresh_hi = self.threshInitial[1]

        img_t = transformA(self.currentFrame.copy(), tracking_blur)
        
        img_mask = threshA(  img_t 
                            ,threshLo = thresh_lo   
                            ,threshHi = thresh_hi ) 

        if not(img_mask is None):

            img_mask = repairA(img_mask, iterations = repair_iterations)

            x,y = find_xy(img_mask)
            radius = find_radius(img_mask)
                    
            if radius > 0:
                self.currentTrackSuccess = True

            self.currentTrackRoi = None  #(x,y,20,20)
            self.currentTrackCircle = (x, y, radius)



if __name__ == "__main__":

    sys.path.append("../")
    from modules.ControlDisplay import Display
    
    cam = cv2.VideoCapture("../data/proc/hello-training-data/output4.avi")
    ret, frame = cam.read()
    
    display = Display()

    trackFactory = TrackFactory(on=True)

    display.setFrame(frame)
    
    trackFactory.setInit(ballColor="green")
    trackFactory.setFrame(frame)
    trackFactory.trackFrame()
    
    roi = trackFactory.getCurrentTrackRoi()
    if roi is not None:
        roi = (int(roi[0]) - 20, int(roi[1]) - 20,  40,  40)
        print roi

    circle = trackFactory.getCurrentTrackCircle()
    print circle
    
    display.setTrack(roiTrack = roi, circleTrack=circle)
    display.drawTrackers()
    
    while(True):
        display.show()
