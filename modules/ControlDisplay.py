import os, sys, time, copy
import numpy as np
import cv2
import argparse

import GlobalsC as g
from GraphicsCV import (draw_annotations, resize_img, draw_rect, draw_circle)
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

    [ ] Control Agenda box with keys

    [ ] add unittests, can't test with guiview_test

Bugs:
    [ ] adjust resize for correct aspect ratio
    [ ] how to cancel an roi request?
    [ ] can't exit on a zoom select request
    [ ] zoom frame is too large; do a max of those dims
    [ ] crop zoom on full frame
    [ ] crop frame before annotations
    [ ] need to erase previous drawn shapes in drawOperators


'''

class Display:

    ''' handles frame display windows '''

    def __init__(self,**kwargs):
        
        self.showOn = True
        self.frameResize = True
        self.frameAnnotateFn = False
        
        self.zoomOn = False
        self.roiSelected = False
        
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
        g.switchRoiMain = False
        g.switchRoiZoom = False

        #reset self.roiSelected to False? no, at new frame


    def setFrame(self, _frame):
        self.frame = _frame.copy()

    def setAnnotateMsg(self, msg):
        self.annotateMsg = copy.copy([msg])

    def alterFrame(self):
        ''' called after each new frame '''        
        
        if self.frameResize:
            self.frame = resize_img(self.frame, True, (640,480))

        if self.frameAnnotateFn:
            self.frame = draw_annotations(self.frame, self.annotateMsg)

        if self.orientation != 0:
            pass    #rotate img

    def drawOperators(self):
        ''' called within the cmd loop '''

        if self.zoomOn and self.zoomRect is not None:
            self.frame = draw_rect(  self.frame
                                    ,self.transformRect(self.zoomRect)
                                    ,color='blue'
                                    ,thick = 1
                                    )

        if self.roiSelected:
            x, y, radius = self.rectToCircle(self.roiRect)
            self.frame = draw_circle(self.frame
                                    ,x
                                    ,y
                                    ,radius
                                    ,color = 'yellow'
                                    ,thick = 3
                                    )

    
    def mainToZoom(self, data):
        ''' convert the coord is main window to the coord in zoom window '''
        #account for orientation
        pass

    @staticmethod
    def transformRect(input_rect):
        ''' (x0,y0, d_x, d_y) -> ((xo,y0),(x1, y1)) 
            note: must be tuples, not lists; to use in opencv functions
        '''

        x = copy.copy(input_rect)            

        rect = ( 
                     ( int(x[0]),       int(x[1]) )
                    ,( int(x[0] + x[2]), int(x[1] + x[3]) )
                )

        return rect

    @staticmethod
    def rectToCircle(input_rect):
        ''' (x0,y0, d_x, d_y) -> (x,y, radius) 
            note: try to create a square for the sake of radius
        '''

        # (x0,y0, d_x, d_y)
        rect = copy.copy(input_rect)            

        x = int( rect[0] + int(rect[2] / 2) )
        y = int( rect[1] + int(rect[3] / 2) )

        radius = min( int(rect[2] / 2), int(rect[3] / 2) )

        return (x, y, radius)
    
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
            if self.cmdSelectZoom:
                self.zoomRect = initBB
                self.zoomOn = True

            if self.cmdSelectRoiMain:
                self.roiRect = initBB
                self.roiSelected = True
        
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

        if self.zoomOn:

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




def test_display_rectToCircle():
    
    rect = (0,0,10,10)
    x,y,r = Display.rectToCircle(rect)

    assert x == 5
    assert y == 5 
    assert r == 5

    rect = (2,1,10,12)
    x,y,r = Display.rectToCircle(rect)

    assert x == 7
    assert y == 7 
    assert r == 5

    rect = (2,1,11,12)
    x,y,r = Display.rectToCircle(rect)

    assert x == 7
    assert y == 7 
    assert r == 5

