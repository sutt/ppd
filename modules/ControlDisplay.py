import os, sys, time, copy
import numpy as np
import cv2
import imutils
import argparse

import GlobalsC as g
from GraphicsCV import (draw_text, resize_img, draw_rect, draw_circle)
from ImgUtils import crop_img

if False: from cv2 import *


'''

Features: 

    [x] orientation adjust
        [x] handle flow thru of bounding box adjust
        [x] position windows side/side vs top/bottom

    [ ] Control Agenda box with keys

Refactors:

    [x] remove hard coded dim size: 640, 320 etc.
    [x] document resize behavior; including resize gy width
    [x] transformRect - > absRect
    [x] comment self data definitions
    [x] better explanation of alterFrame vs drawOperators
    
    [ ] add unittests, can't test with guiview_test
        [ ] test for coord conversion between zoom and main
        [ ] test an actual image for cutting pixels
            [ ] show pixel blending on the border
        [ ] test for resize behavior
        [ ] test mod0 vs not-mod0

Bugs:
    [~] adjust resize for correct aspect ratio
    [ ] how to cancel an roi request?
    [ ] can't exit on a zoom select request
    [x] zoom_display annotation: wrong order
    [~] zoom frame is too large; do a max of those dims


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
        self.orientChanged = False
        
        self.orientPrevious = 0
        
        #this will preserved un-adulterated
        self.origFrame = None
        
        #these will be potenitally resized, annotated, and drawn-on
        # in alterFrames() and drawOperators()
        self.frame = None
        self.zoomFrame = None

        #zoomRect in coord for (resized) frame; relative-rect format
        # (x,y,w,h)
        self.zoomRect = None
        
        #roiRect in coords relative to origFrame; relative-rect format
        # (x,y,w,h)
        self.roiRect = None

        self.roiRectScoring = None
        
        self.selectRectMain = None  #needed this?
        self.selectRectZoom = None  #needed this?
        
        self.annotateMsg = ""
        
        #handle orientation just before show(), and right after selectROI()
        #but otherwise all operations on original orientation
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

        #below this size, zoom_display resizes by a whoole number multiple
        self.modZeroSize = 40
        

    def setOrientation(self, iOrientation):
        if iOrientation not in (90,180,270):
            self.orientation = 0
        else:
            self.orientation = iOrientation

    def reset(self):
        self.zoomOn = False
        self.roiRectScoring = None

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

    def setScoring(self, frameScoring):
        ''' set roiRectScore, is data is in correct form'''
        if frameScoring is None:
            self.roiRectScoring = None
            return
        try:
            assert len(frameScoring) == 4
            assert all( [isinstance(frameScoring[i], int) for i in range(4)] )
        except:
            self.roiRectScoring = None
            return 

        self.roiRectScoring = frameScoring
        self.zoomOn = True
    
    def getScoring(self, bNeedScore):
        ''' return the roiRect data '''
        if not(bNeedScore):
            return None
        if self.roiRect is None:
            return None
        return copy.copy(self.roiRect)

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

        if self.roiRectScoring is not None:
            
            # zoomRect in terms of original
            self.zoomRect =  self.rectOrigToMain(
                                self.zoomInRect(self.roiRectScoring, b_zoomout = True)
                                )
        
        if self.zoomOn:
            self.zoomFrame = self.buildZoomFrame()
            self.alterZoomFrame()
            

    def alterZoomFrame(self):
        ''' make annotation to zoomFrame, but not resize; 
            need to call this each time you do a buildZoomFrame().        
        '''        

        msg = str(self.zoomFrame.shape[:2])
        msg += " <- "
        msg += str(self.rectMainToOrig(self.zoomRect)[2:4][::-1])
        
        if self.zoomFrame.shape[1] % self.rectMainToOrig(self.zoomRect)[2] == 0:
            msg += " mod0"
        
        if self.zoomAnnotateSize:
            self.zoomFrame = draw_text(self.zoomFrame, msg, fontscale = 0.5
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

        if self.roiRectScoring is not None:

            #show scoring data from loaded framenotes
            
            x, y, radius = self.rectToCircle(self.roiToMain(b_scoring=True))
            
            self.frame = draw_circle(self.frame
                                    ,x
                                    ,y
                                    ,radius
                                    ,color = 'red'
                                    ,thick = 2
                                    )

            
            x, y, radius = self.rectToCircle(self.roiToZoom(b_scoring=True))
            
            self.zoomFrame = draw_circle(self.zoomFrame
                                    ,x
                                    ,y
                                    ,radius
                                    ,color = 'red'
                                    ,thick = 1
                                    )

        if self.orientation != 0:

            #rotate images here, to apply minimal amount of coord adjustment
            
            self.frame = imutils.rotate_bound(self.frame
                                            ,self.orientation)

            if self.zoomOn:
                
                self.zoomFrame = imutils.rotate_bound(self.zoomFrame
                                                    ,self.orientation)

            # if self.diffOn:
                #TODO - rotate diff image

                

    
    
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
        
        if self.zoomRect is not None:
            
            if any(map(lambda x: x < self.modZeroSize, 
                        self.rectMainToOrig(self.zoomRect)[2:4])):

                # find a whole number multiple of zoomRect into 320,
                # use that for resize factor
                widthZoom = int( int(self.widthZoomWindow / self.zoomRect[2]) 
                                      * self.zoomRect[2])
        
        zoom_img  = resize_img(zoom_img, True, (widthZoom, heightZoom))

        # resize_img always (?) choses width to resize by, and maintains aspect ratio.
        # Since the zoom_img is always resize larger, if modulo == 0, then every pixel
        # is (presumably?) scaled the exact same amount e.g. 3.0x increase has a 1 pixel 
        # becoming a 3x3 square of the same data-values.
        
        return zoom_img

    def orientCheck(self):
        ''' if orientation has changed, need to destroy old windows
            on first call, it doesn't matter
        '''
        
        #TODO - all windowName cv2.destory here and show() should be a class
        
        PROFILES = (90,270)
        
        if (self.orientation in PROFILES) ^ (self.orientPrevious in PROFILES):
            
            #they have changed; landscape -> profile or vice-versa
            
            windowName = "img_display"
            if self.orientation not in PROFILES:
                windowName += "_profile"

            cv2.destroyWindow(windowName)
                
            if self.zoomOn:
                
                windowName = "zoom_display"
                if self.orientation not in PROFILES:
                    windowName += "_profile"
                
                cv2.destroyWindow(windowName)
                
        self.orientPrevious = self.orientation
    
    def show(self):
        ''' Handle imshow calls, selectROI calls and return handling.
                Also, cvWindow keypress handling.
                
            Note: need to keep entering this function once windows 
                  are created or they become unresponsive.
        '''

        if not(self.showOn):
            return

        self.orientCheck()

        windowName = 'img_display'
        if self.orientation in (90,270): windowName += "_profile"    

        cv2.imshow(windowName, self.frame)
        key = cv2.waitKey(1) & 0xFF

        if self.cmdSelectRoiMain or self.cmdSelectZoom:
            
            windowName = 'img_display'
            if self.orientation in (90,270): windowName += "_profile"    

            rect = cv2.selectROI(windowName, self.frame, True, False )
            
            # frame is rotated at this point so h/w are reversed
            rect = self.adjOrientationRect(rect, self.frame.shape[:2][::-1])
            
            if self.cmdSelectZoom:
                self.zoomRect = rect
                self.zoomOn = True
                self.resetOperators()

            if self.cmdSelectRoiMain:
                self.frame = imutils.rotate_bound(self.frame, - self.orientation)
                self.roiRect = self.rectMainToOrig(rect)
                self.roiSelected = True
                self.resetOperators()
        
        if self.zoomOn and self.windowTwo:
        
            windowName = 'zoom_display'
            if self.orientation in (90,270): windowName += "_profile"    

            cv2.imshow(windowName, self.zoomFrame)
            key2 = cv2.waitKey(1) & 0xFF

        if self.zoomOn and self.cmdSelectRoiZoom and self.windowTwo:
            
            windowName = 'zoom_display'
            if self.orientation in (90,270): windowName += "_profile"    
            
            rect = cv2.selectROI(windowName, self.zoomFrame, True, False)
            
            # zoomFrame is rotated at this point so h/w are reversed
            rect = self.adjOrientationRect(rect, self.zoomFrame.shape[:2][::-1])
            
            #frame and zoomFrame have been rotated already, put back in orig orientation
            self.frame = imutils.rotate_bound(self.frame, -self.orientation)
            self.zoomFrame = imutils.rotate_bound(self.zoomFrame, -self.orientation)
            
            rect = self.rectZoomToOrig(rect)

            self.roiRect = rect 
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

        if self.zoomOn and self.zoomFrame is not None and self.windowTwo:

            if key2 == ord('z'):

                self.zoomRect = self.zoomInRect(copy.copy(self.zoomRect))
                
                self.resetOperators()
                

            if key2 == ord('x'):

                self.zoomRect = self.zoomInRect(copy.copy(self.zoomRect)
                                                ,b_zoomout=True)
                self.resetOperators()
                

    
    # main helpers ---------------------
    # (roiRect (which is relative to origFrame coors) <-> to main/zoom)

    def roiToMain(self, b_scoring=False, input_rect=None):
        ''' return relative-rect roi relative to main-window coord's.
                (since there's no cropping, we only stretch.)
                (we expect the stretch to be modulo-zero as 
                 640 1280 1920 are multiple )
        '''
        rect = copy.copy(self.roiRect)
        
        if b_scoring:
            rect = copy.copy(self.roiRectScoring)

        if input_rect is not None:
            rect = copy.copy(input_rect)

        rectMain = tuple(map(self.scaleOrigToMain, rect))
        
        return rectMain

    def roiToZoom(self, b_scoring=False, input_rect=None):
        ''' return a relative-rect roi relative to zoom-window coord's.
                (there's cropping and stretching.)
                (we don't assume it is modulo-zero; but if it is, 
                 this function should preserve that.)
        '''
        rect = copy.copy(self.roiRect)

        if b_scoring:
            rect = copy.copy(self.roiRectScoring)

        if input_rect is not None:
            rect = copy.copy(input_rect)
        
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

    def rectOrigToMain(self, rectOrig):
        ''' convert rect coords from relative to orig to relative to main
        '''
        rectMain = tuple(map(self.scaleOrigToMain, rectOrig))
        return rectMain

    @staticmethod
    def zoomInRect(rect, zoomFct = 0.1, b_zoomout=False):

        zoomFct = 0.1
        c = 1
        
        if b_zoomout: 
            zoomFct = 1 - (1.0/(1.0 + zoomFct))  #~0.09
            c = -1

        deltaW, deltaH = zoomFct * rect[2], zoomFct * rect[3]

        rect = (
                 int(round(rect[0] + (deltaW * c)))
                ,int(round(rect[1] + (deltaH * c)))
                ,int(round(rect[2] - 2*(deltaW * c)))
                ,int(round(rect[3] - 2*(deltaH * c)))
               )

        return rect

    
    def adjOrientationRect(self, rect, (imgH, imgW)):
        ''' adjusting bounding box from selectROI into original images orientation '''
        
        if self.orientation == 0:
            return rect
        
        x, y, dx, dy = rect
        
        h, w = imgH, imgW

        if self.orientation == 90:
        
            x_new = y
            y_new =  h - (dx + x)
            dx_new = dy
            dy_new = dx

        elif self.orientation == 180:
            
            x_new = -dx + h - x
            y_new = -dy + w - y
            dx_new = dx
            dy_new = dy

        elif self.orientation == 270:
            
            x_new = w - (dy + y)
            y_new =  x
            dx_new = dy
            dy_new = dx

        else:
            return rect
        
        return (x_new, y_new, dx_new, dy_new)

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



if __name__ == "__main__" and False:
    
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
    pass
    # test_display_zoom_crop_1()
    # test_rotate_1()

    #resizeIt
    #cropIt 
    #roiSelectIt, 
    
    # assert all([pix == (255,255,255)  for pix in cropped_region])

    