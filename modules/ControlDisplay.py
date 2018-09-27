import os, sys, time, copy
import numpy as np
import cv2
import argparse

import GlobalsC as g
from GraphicsCV import (draw_annotations, resize_img, draw_rect)
from ImgUtils import crop_img

if False: from cv2 import *


'''

Features: 
    [ ] Zoom Window
        [x] gui cmd: selectZoom
        [ ] further zoom in/out with keypress on zoom window
        [ ] select roi in zoom window
            [ ] draw roi in main
        [ ] zoom:blue, roi:yellow
    
    [ ] orientation adjust
        [ ] handle flow thru of bounding box adjust

    [ ] add unittests, can't test with guiview_test

Bugs:
    [ ] adjust resize for correct aspect ratio
    [ ] how to cancel an roi request?
    [ ] can't exit on a zoom select request
    [ ] zoom frame is too large; do a max of those dims
    [ ] crop zoom on full frame
    [ ] crop frame before annotations


'''

class Display:

    ''' handles frame display windows '''

    def __init__(self,**kwargs):
        
        self.showOn = True
        self.frameResize = True
        self.frameAnnotateFn = False
        
        self.zoomOn = False
        
        self.frame = None

        self.zoomRect = None
        self.selectRectMain = None
        self.selectRectZoom = None
        
        self.annotateMsg = ""
        self.orientation = 0

        self.cmdSelectZoom = False
        self.cmdSelectRoiMain = False
        self.cmdSelectRoiZoom = False

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

    def setCmd( self
                ,cmdSelectZoom=False
                ,cmdSelectRoiMain=False
                ,cmdSelectRoiZoom=False
                ):
        
        self.cmdSelectZoom = cmdSelectZoom
        self.cmdSelectRoiMain = cmdSelectRoiMain
        self.cmdSelectRoiZoom = cmdSelectRoiZoom

        g.switchZoom = False


    def setFrame(self, _frame):
        self.frame = _frame.copy()

    def setAnnotateMsg(self, msg):
        self.annotateMsg = copy.copy([msg])

    def alterFrame(self):
        
        if self.frameResize:
            self.frame = resize_img(self.frame, True, (640,480))

        if self.frameAnnotateFn:
            self.frame = draw_annotations(self.frame, self.annotateMsg)

        if self.zoomOn and self.zoomRect is not None:
            self.frame = draw_rect(  self.frame
                                    ,self.transformRect(self.zoomRect)
                                    ,color='blue'
                                    ,thick = 1
                                    )

        if self.orientation != 0:
            pass    #rotate img
    
    @staticmethod
    def transformRect(input_rect):
        ''' (x0,y0, d_x, d_y) -> ((xo,y0),(x1, y1)) '''

        x = copy.copy(input_rect)            

        rect = ( 
                     ( int(x[0]),       int(x[1]) )
                    ,( int(x[0] + x[2]), int(x[1] + x[3]) )
                )

        return rect
    
    def buildZoomFrame(self):
        
        if self.zoomRect is None:
            
            zoom_img = np.zeros(self.frame.shape)
            zoom_img = draw_annotations(zoom_img, ["n/a"])
        
        else:
            
            zoom_img = crop_img(self.frame, self.transformRect(self.zoomRect))

        zoom_img  = resize_img(zoom_img, True, (320,240))

        return zoom_img

    def show(self):
        
        # need to keep entering this function once windows are created or
        # they become unresponsive

        if not(self.showOn):
            return

        windowName = 'img_display'
        cv2.imshow(windowName, self.frame)
        key = cv2.waitKey(1) & 0xFF

        if self.cmdSelectRoiMain or self.cmdSelectZoom:
            initBB = cv2.selectROI("img_display", self.frame, True, False )
            print initBB
            self.zoomRect = initBB
            self.zoomOn=True
        
        if self.zoomOn:
            windowName = 'zoom_display'
            cv2.imshow(windowName, self.buildZoomFrame())
            key2 = cv2.waitKey(1) & 0xFF

        if self.zoomOn and self.cmdSelectRoiZoom:
            initBB = cv2.selectROI("zoom_display", self.frame, True, False )
            #TODO - add selectRoiZoom logic
            

        if key == ord("s"):
            initBB = cv2.selectROI("img_display", self.frame, True, False )
            print initBB
            
        if key2 == ord('z'):
            pass
            #TODO - add more zoom

        if key2 == ord('x'):
            pass
            #TODO - add less zoom

if __name__ == "__main__":
    
    display = Display()
    display.setInit(showOn=True, frameResize=True, frameAnnotateFn=True)
    
    vidPathFn = "../data/proc/hello-training-data/output4.avi"
    vidPathFn = "../data/proc/hello-training-data/output7.avi"
    cam = cv2.VideoCapture(vidPathFn)

    ret, frame = cam.read()

    display.setFrame(frame)
    display.setAnnotateMsg("dummy")
    display.alterFrame()

    i = 0
    while(True):
        display.show()
        
        i += 1
        if i % 5*10**2 == 0:
            print 'cmdSelectZoom'
            display.setCmd(cmdSelectZoom=True)
        

    cv2.destroyAllWindows()


