import os, sys, time, copy
import numpy as np
import cv2
import argparse

from GraphicsCV import (draw_annotations, resize_img)

if False: from cv2 import *

class Display:

    def __init__(self,**kwargs):
        
        self.showOn = True
        self.frameResize = True
        self.frameAnnotateFn = False
        
        self.frame = None
        
        self.annotateMsg = ""
        self.orientation = 0

    def setOrientation(iOrientation):
        if iOrientation not in (90,180,270):
            self.iOrientation = 0
        else:
            self.orientation = iOrientation

    def setInit( self
                ,showOn=True
                ,frameResize=True
                ,frameAnnotateFn=True
                ):

        self.showOn = showOn
        self.frameResize = frameResize
        self.frameAnnotateFn = frameAnnotateFn

    def setFrame(self, _frame):
        self.frame = _frame.copy()

    def setAnnotateMsg(self, msg):
        self.annotateMsg = copy.copy([msg])

    def alterFrame(self):
        
        if self.frameResize:
            self.frame = resize_img(self.frame, True, (640,480))

        if self.frameAnnotateFn:
            self.frame = draw_annotations(self.frame, self.annotateMsg)

        if self.orientation != 0:
            pass    #rotate img
    
    def show(self):

        if not(self.showOn):
            return

        windowName = 'img_display'
        cv2.imshow(windowName, self.frame)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord("s"):
            initBB = cv2.selectROI("img_display", self.frame, True, False )
            print initBB
            
        if key == ord('q'):
            pass
            # break

if __name__ == "__main__":
    
    display = Display()
    display.setInit(showOn=True, frameResize=True, frameAnnotateFn=True)
    
    vidPathFn = "data/proc/hello-training-data/output4.avi"
    cam = cv2.VideoCapture(vidPathFn)

    ret, frame = cam.read()

    display.setFrame(frame)
    display.setAnnotateMsg("dummy")
    display.alterFrame()

    while(True):
        display.show()

    cv2.destroyAllWindows()


