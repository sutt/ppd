import os, sys, time, copy
import numpy as np
import cv2
import argparse

import GlobalsC as g
from GraphicsCV import (draw_text, resize_img, draw_rect, draw_circle)
from ImgUtils import crop_img

if False: from cv2 import *


'''

Features: 
    [ ] Zoom Window
        [x] gui cmd: selectZoom
        [ ] further zoom in/out with keypress on zoom window
        [x] select roi in zoom window
            [x] draw roi in main
        [x] zoom:blue, roi:yellow
        [x] annotate with zoomwindow pixel size
            [x] pixels in window, nums pixels in original
        [x] return from drawOperator if not nec
        [x] window3, diff
        [x] zoom on/off by gui
        [x] crop from full size image
        [ ] zero-modulo resize should be default under certain size zoomFrame

    [ ] orientation adjust
        [ ] handle flow thru of bounding box adjust
        [ ] position windows side/side vs top/bottom

    [ ] Control Agenda box with keys

Refactors:

    [x] remove hard coded dim size: 640, 320 etc.
    [ ] document resize behavior
    [x] transformRect - > absRect
    [x] comment self data definitions
    [ ] better explanation of alterFrame vs drawOperators
    
    [ ] add unittests, can't test with guiview_test
        [ ] test for coord conversion between zoom and main
        [ ] test an actual image for cutting pixels
            [ ] show pixel blending on the border
        [ ] test for resize behavior

Bugs:
    [ ] adjust resize for correct aspect ratio
    [ ] how to cancel an roi request?
    [ ] can't exit on a zoom select request
    [ ] zoom frame is too large; do a max of those dims
    [x] crop zoom on full frame
    [x] crop frame before annotations
    [x] need to erase previous drawn shapes in drawOperators
    [x] zoom isn't cropped after selectroi


'''

class Display:

    ''' handles frame display windows '''

    def __init__(self,**kwargs):
        
        self.showOn = True
        self.frameResize = True
        self.frameAnnotateFn = False
        self.zoomAnnotateSize = True
        
        self.zoomOn = False
        self.roiSelected = False
        
        #this will preserved un-adulterated
        self.origFrame = None
        
        #these will be potenitally resized, annotated, and drawn-on
        # in alterFrames() and drawOperators()
        self.frame = None
        self.zoomFrame = None

        #zoomRect in coord for (resized) frame; relative-rect format
        self.zoomRect = None
        
        #roiRect in coords relative to origFrame; relative-rect format
        self.roiRect = None
        
        self.selectRectMain = None  #needed this?
        self.selectRectZoom = None  #needed this?
        
        self.annotateMsg = ""
        self.orientation = 0

        self.cmdSelectZoom = False
        self.cmdSelectRoiMain = False
        self.cmdSelectRoiZoom = False

        self.windowTwo = True
        self.windowThree = False

        self.widthMainWindow = 640
        self.heightMainWindow = 480
        self.widthZoomWindow = 320
        self.heightZoomWindow = 240
        

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
                ,windowTwo=None
                ,windowThree=None
                ):
        
        self.cmdSelectZoom = cmdSelectZoom
        self.cmdSelectRoiMain = cmdSelectRoiMain
        self.cmdSelectRoiZoom = cmdSelectRoiZoom

        if windowTwo is not None:
            self.windowTwo = windowTwo
        if windowThree is not None:
            self.windowThree = windowThree

        g.switchZoom = False
        g.switchRoiMain = False
        g.switchRoiZoom = False

        if not(g.windowTwo):
            cv2.destroyWindow("zoom_display")

        if not(g.windowThree):
            cv2.destroyWindow("diff_display")


    def setFrame(self, _frame):
        self.frame = _frame.copy()
        self.origFrame = _frame.copy()

    def getOrigFrame(self):
        return self.origFrame
    
    def setAnnotateMsg(self, msg):
        self.annotateMsg = copy.copy(msg)

    def alterFrame(self):
        ''' make changes to frame, including resize. also, build zoomFrame here.
            need to call this every new frame and on resetOperators
        '''        
        
        if self.frameResize:
            self.frame = resize_img(self.frame, True, 
                                    (self.widthMainWindow,self.heightMainWindow))

        if self.frameAnnotateFn:
            self.frame = draw_text(self.frame, self.annotateMsg)

        if self.orientation != 0:
            pass   

        if self.zoomOn:
            self.zoomFrame = self.buildZoomFrame()
            self.alterZoomFrame()

    def alterZoomFrame(self):
        ''' make annotation to zoomFrame, but not resize; 
            need to call this each time you do a buildZoomFrame().        
        '''        

        msg = str(self.zoomFrame.shape[:2])
        msg += " orig: "
        msg += str(self.rectMainToOrig(self.zoomRect)[2:4])
        # if self.zoomModuloZero:
        #     msg += " mod0"
        
        if self.zoomAnnotateSize:
            self.zoomFrame = draw_text(self.zoomFrame, msg, fontscale = 0.6
                                       ,color= (0,0,0), b_bottom=True)

        if self.orientation != 0:
            pass    #rotate img


    def resetOperators(self):
        ''' every user/gui action that changes a frame will refresh the frames
            and draw everything again'''

        self.frame = self.getOrigFrame()
        self.alterFrame()
        self.drawOperators()
        
    
    def drawOperators(self):
        ''' Draw onto frame(s) based on user input.
            This has to be called for every new frame.
            And everytime user/gui changes zoomRect or roiRect; resetOperators()
        '''

        if self.zoomOn and self.zoomRect is not None:
            
            self.frame = draw_rect(  self.frame
                                    ,self.absRect(self.zoomRect)
                                    ,color='blue'
                                    ,thick = 1
                                    )

        if self.roiSelected:
            
            x, y, radius = self.rectToCircle(self.roiToMain())
            
            self.frame = draw_circle(self.frame
                                    ,x
                                    ,y
                                    ,radius
                                    ,color = 'yellow'
                                    ,thick = 3
                                    )
            # because when mainwindow has resize, modulo might not be 0,
            # so roiToMain in that case isn't a perfect match. But for 640 1280 1920, 
            # they are perfect modulo, so it should be a match

        if self.roiSelected and self.zoomOn:
            
            x, y, radius = self.rectToCircle(self.roiToZoom())
            
            self.zoomFrame = draw_circle(self.zoomFrame
                                    ,x
                                    ,y
                                    ,radius
                                    ,color = 'yellow'
                                    ,thick = 1
                                    )
            # because when zoomwindow has resize, modulo might not be 0,
            # but whether it is or isn't, is decided in buildZoomFrame()
            # with the choice of width
    
    
    def buildZoomFrame(self):
        
        if self.zoomRect is None:
            
            zoom_img = np.zeros(self.frame.shape)
            zoom_img = draw_text(zoom_img, "n/a")
        
        else:
            
            zoom_img = crop_img( self.getOrigFrame()
                                ,self.absRect(
                                    tuple( 
                                     self.scaleMainToOrig(p) for p in self.zoomRect
                                        )
                                    )
                                )
            
            # this does not alter pixels, it is still directly derived
            # from origFrame
        
        widthZoom, heightZoom = self.widthZoomWindow,self.heightZoomWindow
        
        #TODO - adjust for modulo zoom
        
        zoom_img  = resize_img(zoom_img, True, (widthZoom, heightZoom))

        # since the zoom_img is always resize larger, if modulo == 0, then every pixel
        # is (presumably?) scaled the exact same amount e.g. 3.0x increase has a 1 pixel 
        # becoming a 3x3 square of the same data-values.
        
        return zoom_img

    
    def show(self):
        ''' Handle imshow calls, selectROI calls and return handling.
                Also, cvWindow keypress handling.
                
            Note: need to keep entering this function once windows 
                  are created or they become unresponsive.
        '''

        if not(self.showOn):
            return

        windowName = 'img_display'
        cv2.imshow(windowName, self.frame)
        key = cv2.waitKey(1) & 0xFF

        if self.cmdSelectRoiMain or self.cmdSelectZoom:
            
            rect = cv2.selectROI("img_display", self.frame, True, False )
            
            if self.cmdSelectZoom:
                self.zoomRect = rect
                self.zoomOn = True
                self.resetOperators()

            if self.cmdSelectRoiMain:
                self.roiRect = self.rectMainToOrig(rect)
                self.roiSelected = True
                self.resetOperators()
        
        if self.zoomOn and self.windowTwo:
        
            windowName = 'zoom_display'
            cv2.imshow(windowName, self.zoomFrame)
            key2 = cv2.waitKey(1) & 0xFF

        if self.zoomOn and self.cmdSelectRoiZoom and self.windowTwo:
            
            rect = cv2.selectROI("zoom_display", self.zoomFrame, True, False )

            self.roiRect = self.rectZoomToOrig(rect)
            self.roiSelected = True
            self.resetOperators()

            # we don't need to ensure modulo-zero here, that has already been 
            # enforced (or not) in the choice of zoomFrame-width in buildZoomFrame()

        if self.windowThree:

            windowName = 'diff_display'
            cv2.imshow(windowName, self.zoomFrame)  #TODO add diffFrame
            key2 = cv2.waitKey(1) & 0xFF

        #new func -----------
        if key == ord("s"):
            initBB = cv2.selectROI("img_display", self.frame, True, False )

        # if self.zoomOn and self.zoomFrame is not None:

        #     if key2 == ord('z'):
        #         pass
        #         #TODO - add more zoom

        #     if key2 == ord('x'):
        #         pass
        #         #TODO - add less zoom

    
    # main helpers ---------------------
    # (roiRect (which is relative to origFrame coors) <-> to main/zoom)

    def roiToMain(self):
        ''' return relative-rect roi relative to main-window coord's.
                (since there's no cropping, we only stretch.)
                (we expect the stretch to be modulo-zero as 
                 640 1280 1920 are multiple )
        '''
        rect = copy.copy(self.roiRect)
        rectMain = tuple(map(self.scaleOrigToMain, rect))
        return rectMain

    def roiToZoom(self):
        ''' return a relative-rect roi relative to zoom-window coord's.
                (there's cropping and stretching.)
                (we don't assume it is modulo-zero; but if it is, 
                 this function should preserve that.)
        '''
        rect = copy.copy(self.roiRect)
        
        #orig->main
        x0, y0, dx, dy = map(self.scaleOrigToMain, rect)  
        
        #main->zoom
        x0,y0 = self.coordMainToZoom((x0,y0))
        x0 = self.scaleMainToZoom(x0)
        y0 = self.scaleMainToZoom(y0)
        dx = self.scaleMainToZoom(dx)
        dy = self.scaleMainToZoom(dy)

        rectZoom = (x0, y0, dx, dy)
        
        return rectZoom

    def rectZoomToOrig(self, rectZoom):
        ''' convert rect coords from relative to zoom to relative to orig
        '''
        x0, y0, dx, dy = rectZoom

        #zoom->main
        x0 = self.scaleZoomToMain(x0)
        y0 = self.scaleZoomToMain(y0)
        dx = self.scaleZoomToMain(dx)   
        dy = self.scaleZoomToMain(dy)   
        x0, y0 = self.coordZoomToMain((x0,y0))
    
        #main->orig
        rectMain = (x0, y0, dx, dy)
        rectOrig = tuple(map(self.scaleMainToOrig, rectMain))
        
        return rectOrig

    def rectMainToOrig(self, rectMain):
        ''' convert rect coords from relative to main to relative to orig
        '''
        rectOrig = tuple(map(self.scaleMainToOrig, rectMain))
        return rectOrig

    
    # helpers for the helpers: --------------
    # (adjust individual coords or individual values)
    def coordMainToZoom(self, coord_xy):
        ''' convert the coord (a tuple of integers) in main window 
            to the coord in zoom window '''
        
        #TODO - account for orientation
        
        x = coord_xy[0] - self.zoomRect[0]
        y = coord_xy[1] - self.zoomRect[1]

        return x,y

    def coordZoomToMain(self, coord_xy):
        ''' convert the coord (a tuple of integers) in zoom window 
            to the coord in main window '''
        
        #TODO - account for orientation
        
        x = coord_xy[0] + self.zoomRect[0]
        y = coord_xy[1] + self.zoomRect[1]

        return x,y

    def scaleOrigToMain(self, val):
        ''' convert val (an integer) from origFrame to (potentially resized) 
            main window frame.
                (assume proportional resize took place) 
                (round nearest as we don't assume modulo-zero resize) '''
        adj_factor = float(self.frame.shape[1]) / float(self.origFrame.shape[1])
        adj_val = round(float(val)*adj_factor, 0)
        return int(adj_val)

    def scaleMainToOrig(self, val):
        ''' convert val (an integer) from origFrame to (potentially resized) 
            main window frame.
                (assume proportional resize took place) 
                (round nearest as we don't assume modulo-zero resize) '''
        adj_factor = float(self.origFrame.shape[1]) / float(self.frame.shape[1])
        adj_val = round(float(val)*adj_factor, 0)
        return int(adj_val)

    def scaleMainToZoom(self, val):
        ''' a stretch transform: does rounding nearest for non modulo-zero '''
        adj_factor = float(self.zoomFrame.shape[1]) / float(self.zoomRect[2])
        adj_val = round(float(val)*adj_factor, 0)    
        return int(adj_val)

    def scaleZoomToMain(self, val):
        ''' a stretch transform: does rounding nearest for non modulo-zero '''
        adj_factor = float(self.zoomRect[2]) / float(self.zoomFrame.shape[1])
        adj_val = round(float(val)*adj_factor,0)
        return int(adj_val)
    
    # shape helpers ------------------
    
    @staticmethod
    def absRect(input_rect):
        ''' takes an (opencv style) relative rect, returns an absolute rect.
                (x0,y0, d_x, d_y) -> ((xo,y0),(x1, y1)) 
                note: must be tuples, not lists; to use in opencv functions
        '''

        x = copy.copy(input_rect)            

        rect = ( 
                     (
                         int(x[0])
                        ,int(x[1]) 
                     )
                    ,( 
                         int(x[0] + x[2])
                        ,int(x[1] + x[3]) 
                     )
                )

        return rect

    @staticmethod
    def rectToCircle(input_rect):
        ''' takes relative-format rect, fits a circle inside it
            (x0,y0, d_x, d_y) -> (x,y, radius) 
            note: try to create a square for the sake of radius
        '''

        # (x0,y0, d_x, d_y)
        rect = copy.copy(input_rect)            

        x = int( rect[0] + int(rect[2] / 2) )
        y = int( rect[1] + int(rect[3] / 2) )

        radius = min( int(rect[2] / 2), int(rect[3] / 2) )

        return (x, y, radius)



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
    display.zoomOn = True

    cmdSelectZoom = False
    cmdSelectRoiMain = False
    cmdSelectRoiZoom = False

    display.zoomOn = True   #debugZoom

    i = 0
    while(True):

        #to debug pause and set these in console
        display.setCmd(cmdSelectZoom=cmdSelectZoom
                        ,cmdSelectRoiMain=cmdSelectRoiMain
                        ,cmdSelectRoiZoom=cmdSelectRoiZoom
                        )
        
        display.alterFrame()
        
        display.drawOperators()
        
        display.show()
        
        i += 1
        if i % 5*10**3 == 0:
            
            display.rectZoom = (20,20, 40,40)   #debugZoom
        #     print 'cmdSelectZoom'
        #     display.setCmd(cmdSelectZoom=True)
        

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

def test_display_zoom1():
    ''' test how image resizing works '''
    pass
    
    # assert img.shape == (320, 240)

def test_display_zoom_crop_1():
    ''' send picture data thru, see the transforms '''
    
    #test data
    X,Y = 480,640
    x0,x1 = 150,250
    y0,y1= 300,400

    rect = (x0,y0,x1,y1)
    img = np.zeros(shape=(X,Y,3))
    img = np.array(img, dtype=np.uint8)
    for x in range(x0,x1):
        for y in range (y0,y1):
            img[x,y] = np.array([255,255,255] ,dtype=np.uint8)

    #dont even need the actual image here; just go off roiRect

    ZOOM = (100,100,200,200)
    ROI = (150, 200, 120, 170)
    
    display = Display()
    display.setInit(showOn=True)
    display.setFrame(img)
    display.zoomOn = True
    display.zoomRect = ZOOM
    display.roiRect = ROI
    display.resetOperators()
    
    x0, y0, dx, dy = copy.copy(ROI)
    x0,y0 = display.coordMainToZoom((x0,y0))
    x0,y0 = display.scaleMainToZoom(x0), display.scaleMainToZoom(y0)
    dx, dy = display.scaleMainToZoom(dx), display.scaleMainToZoom(dy)
    rectZoom = (x0, y0, dx, dy)

    display.drawOperators()
    while(True):
        display.show()

    assert rectZoom == (1)

if __name__ == "__main__":
    test_display_zoom_crop_1()


    #resizeIt
    #cropIt 
    #roiSelectIt, 
    
    # assert all([pix == (255,255,255)  for pix in cropped_region])

    