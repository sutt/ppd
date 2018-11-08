import os, sys, time, copy
import numpy as np
import cv2
import imutils
import argparse

from DataSchemas import ScoreSchema
import GlobalsC as g
from GraphicsCV import (draw_text, resize_img, draw_rect, draw_circle
                        ,draw_ray, convert_color)
from ImgUtils import crop_img

if False: from cv2 import *


'''

Features: 

    [ ] New resize method for when score_display wants to be vertical

Refactors:

    [ ] only build "n/a" zoom frame once
    
    [ ] add unittests, can't test with guiview_test
        [ ] test for coord conversion between zoom and main
        [ ] test an actual image for cutting pixels
            [ ] show pixel blending on the border
        [ ] test for resize behavior
        [ ] test mod0 vs not-mod0

Bugs:
    [ ] how to cancel an roi request?
    [ ] on --file, after reopen file zoomOn is off so zoom_display is frozen
    [ ] can't z/x zoom unzoom with tracking roi
    [ ] in a --dir run, old zoomframe can be OOB for new vid's frames
        "#BUG-check if zoomRect is in bounds in new video"



'''

class Display:

    ''' handles frame display windows '''

    def __init__(self,**kwargs):
        
        self.showOn = True
        self.frameResize = True
        self.frameAnnotateFn = False
        self.zoomAnnotateSize = True
        
        self.zoomOn = False
        self.scoreOn = False
        self.scoreOff = False   #TODO - refactor to bShowScoring
        self.trackOn = False
        self.roiSelected = False
        self.orientChanged = False
        
        self.orientPrevious = 0
        
        #this will preserved un-adulterated
        self.origFrame = None
        
        #these will be potenitally resized, annotated, and drawn-on
        # in alterFrames() and drawOperators()
        self.frame = None
        self.zoomFrame = None
        self.scoreFrame = None

        #zoomRect in coord for (resized) frame; relative-rect format
        # (x,y,w,h)
        self.zoomRect = None
        
        #scoreRect formatted like zoomRect, but is for current-tracking-roi
        # and for scoring-roi from metalog
        self.scoreRect = None

        #input: notes -> display
        self.inputScore = ScoreSchema()

        #output: display -> notes
        self.outputScore = ScoreSchema()

        #trackFactory -> this class
        self.trackScore = ScoreSchema()
        
        self.selectRectMain = None  #needed this?
        self.selectRectZoom = None  #needed this?
        
        self.annotateMsg = ""
        
        #handle orientation just before show(), and right after selectROI()
        #but otherwise all operations on original orientation
        self.orientation = 0

        self.cmdSelectZoom = False
        self.cmdSelectRoiMain = False
        self.cmdSelectRoiZoom = False
        self.cmdSelectReset = False

        # what does hand-score represent:
        self.trackObjEnum = 0   # objects: 0,1,2,3
        self.trackTypeEnum = 0   # 0=circle, 1=ray

        self.windowTwo = True
        self.windowThree = True
        
        self.bShowScoring = False
        self.bAnnotateObjEnum = False

        self.scoreDisplayObjEnum = 0

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

    def setScoreDisplayObjEnum(self, scoreDisplayObjEnum):
        self.scoreDisplayObjEnum = int(scoreDisplayObjEnum)

    def reset(self):
        self.inputScore.reset()
        # self.zoomOn = False
        #BUG-check if zoomRect is in bounds in new video
        
    def setInit( self
                ,showOn=True
                ,scoreOff=False
                ,frameResize=True
                ,frameAnnotateFn=True
                ):

        self.showOn = showOn
        self.scoreOff = scoreOff
        self.frameResize = frameResize
        self.frameAnnotateFn = frameAnnotateFn

    def setShowScoring(self, bShowScoring):
        self.bShowScoring = bShowScoring

    def getShowScoring(self):
        return self.bShowScoring

    def setCmd( self
                ,cmdSelectZoom=False
                ,cmdSelectRoiMain=False
                ,cmdSelectRoiZoom=False
                ,trackObjEnum=0
                ,trackTypeEnum=0
                ,windowTwo=None
                ,windowThree=None
                ,annotateObjEnum=None
                ,cmdSelectReset=False
                ,globalsOn=True
                ):
        
        self.cmdSelectZoom = cmdSelectZoom
        self.cmdSelectRoiMain = cmdSelectRoiMain
        self.cmdSelectRoiZoom = cmdSelectRoiZoom
        self.cmdSelectReset = cmdSelectReset

        self.trackObjEnum = trackObjEnum
        self.trackTypeEnum = trackTypeEnum
        
        if windowTwo is not None:
            self.windowTwo = windowTwo
        if windowThree is not None:
            self.windowThree = windowThree
        
        if annotateObjEnum is not None:
            
            if self.bAnnotateObjEnum != annotateObjEnum:
                self.bAnnotateObjEnum = annotateObjEnum
                self.resetOperators()

        if cmdSelectReset:

            self.outputScore.reset()
            self.resetOperators()

        if globalsOn:
            
            g.switchZoom = False
            g.switchRoiMain = False
            g.switchRoiZoom = False
            g.switchSelectReset = False

            if not(g.windowTwo):
                cv2.destroyWindow("zoom_display")

            if not(g.windowThree):
                cv2.destroyWindow("diff_display")


    def setFrame(self, _frame):
        self.frame = _frame.copy()
        self.origFrame = _frame.copy()

    def getOrigFrame(self):
        return self.origFrame

    def getOrigFrameDims(self):
        return self.origFrame.shape[:2]
    
    def setAnnotateMsg(self, msg):
        self.annotateMsg = copy.copy(msg)

    def setScoring(self, frameScoring):
        ''' set roiRectScoring, if data is in correct form'''
        if frameScoring is None:
            self.inputScore.reset()
            return
        
        self.inputScore.load(frameScoring)
        self.scoreOn = True
    
    def getScoring(self, bNeedScore):
        ''' return the roiRect data '''
        if bNeedScore:
            return self.outputScore.getAll()
        return None

    def alterFrame(self):
        ''' make changes to frame, including resize. also, build zoomFrame and scoreFrame.
            need to call this every new frame and on resetOperators
        '''        
        
        if self.frameResize:
            self.frame = resize_img(self.frame, True, 
                                    (self.widthMainWindow,self.heightMainWindow))

        if self.frameAnnotateFn:
            self.frame = draw_text(self.frame, self.annotateMsg)

        #TODO
        # if self.frameAnnotateTrackSuccess:
        #     _color = 'blue' if self.circleTrack is not None else 'red'
        #     self.frame = draw_rect(self.frame, (2,2,10,10), color = _color)

        if not(self.scoreOff):
            
            protoZoomRect = None
            
            if self.inputScore.getData(self.scoreDisplayObjEnum) is not None:               
                protoZoomRect = self.inputScore.getObjRect(self.scoreDisplayObjEnum)
                zoomFct = 0.1
                
            elif self.trackScore.checkHasContents():    
                protoZoomRect = self.trackScore.getObjRect(self.scoreDisplayObjEnum)
                zoomFct = 0.3   

            if protoZoomRect is None:
                self.scoreRect = None
            
            elif protoZoomRect[2] < 1 or protoZoomRect[3] < 1:
                self.scoreRect = None
                
            else:

                protoZoomRect = self.minDimsForRect(
                                             protoZoomRect
                                            ,self.getOrigFrameDims()
                                            ,min_scalar_width = 10
                                            ,max_multiple_width = 3
                                                    )

                self.scoreRect =  self.rectOrigToMain(
                                    self.zoomInRect( protoZoomRect
                                                    ,b_zoomout = True
                                                    ,zoomFct = zoomFct
                                                    )
                                                )

        if self.zoomOn: 
            self.zoomFrame = self.buildZoomFrame()
            self.alterZoomFrame()

        if ((self.scoreOn and not(self.scoreOff) and self.bShowScoring)
            or self.trackOn):
            self.scoreFrame = self.buildScoreFrame()
            self.alterScoreFrame()
            

    def alterZoomFrame(self):
        ''' make annotation to zoomFrame, but not resize; 
            need to call this each time you do a buildZoomFrame().        
        '''        

        if self.zoomRect is None or self.zoomFrame is None:
            return

        msg = str(self.zoomFrame.shape[:2])
        msg += " <- "
        msg += str(self.rectMainToOrig(self.zoomRect)[2:4][::-1])
        
        if self.zoomFrame.shape[1] % self.rectMainToOrig(self.zoomRect)[2] == 0:
            msg += " mod0"
        
        if self.zoomAnnotateSize:
            self.zoomFrame = draw_text(self.zoomFrame, msg, fontscale = 0.5
                                       ,color= (0,0,0), b_bottom=True)

    def alterScoreFrame(self):
        ''' make annotation to scoreFrame, but not resize; 
            need to call this each time you do a buildScoreFrame().        
        '''        

        if self.scoreRect is None or self.scoreFrame is None:
            return

        msg = str(self.scoreFrame.shape[:2])
        msg += " <- "
        msg += str(self.rectMainToOrig(self.scoreRect)[2:4][::-1])
        
        if self.scoreFrame.shape[1] % self.rectMainToOrig(self.scoreRect)[2] == 0:
            msg += " mod0"
        
        if self.zoomAnnotateSize:
            self.scoreFrame = draw_text(self.scoreFrame, msg, fontscale = 0.5
                                       ,color= (0,0,0), b_bottom=True)




    def resetOperators(self):
        ''' every user/gui action that changes a frame will refresh the frames
            and draw everything again'''

        self.frame = self.getOrigFrame()
        self.alterFrame()
        self.drawOperators()
        self.drawTrackers()
        self.adjustOrient()
        
    
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

        if self.outputScore.checkHasContents():
            
            self.drawOntoPane( frame=self.frame
                              ,data=self.outputScore
                              ,coordsRelative='origToMain'
                              ,color='yellow'
                              ,thick=3
                              ,b_annotate = self.bAnnotateObjEnum)
            
            # because when mainwindow has resize, modulo might not be 0,
            # so roiToMain in that case isn't a perfect match. But for 640 1280 1920, 
            # they are perfect modulo, so it should be a match

        # if self.roiSelected and self.zoomOn:
        if self.outputScore.checkHasContents() and self.zoomOn:

            self.drawOntoPane( frame=self.zoomFrame
                              ,data=self.outputScore
                              ,coordsRelative='origToZoom'
                              ,color='yellow'
                              ,thick=1)
            # because when zoomwindow has resize, modulo might not be 0,
            # but whether it is or isn't, is decided in buildZoomFrame()
            # with the choice of width

        # if self.roiRectScoring is not None:
        if self.inputScore.checkHasContents() and self.bShowScoring:

            self.drawOntoPane( frame=self.frame
                              ,data=self.inputScore
                              ,coordsRelative='origToMain'
                              ,color='blue'
                              ,thick=2
                              ,b_annotate = self.bAnnotateObjEnum)

            
            if self.scoreRect is not None and not(self.scoreOff):
    
                self.drawOntoPane(frame=self.scoreFrame
                              ,data=self.inputScore
                              ,coordsRelative='origToScore'
                              ,color='blue'
                              ,thick=1)

                

    def drawOntoPane(self, frame, data, coordsRelative, color, thick, b_annotate=False):
        ''' draw both circle and ray shapes within [score]data onto a frame here:

                frame - (np.array) reference to the frame to be dwarn upon
                data - (ScoreSchema) either inputScore or outputScore
                coordsRelative (str) the type of coords transform to perform before draw
                color (str), thick (int) - formatting params
        '''

        for _circleObj in data.getListType('circle'):

            _circleEnum, _circleData = _circleObj
                
            if coordsRelative == 'origToMain':
                rect = self.roiToMain(input_rect = _circleData)
            
            elif coordsRelative == 'origToZoom':
                rect = self.roiToZoom(input_rect = _circleData)

            elif coordsRelative == 'origToScore':
                rect = self.roiToScore(input_rect= _circleData)

            x, y, radius = self.rectToCircle(rect)
        
            frame = draw_circle(frame
                                ,x
                                ,y
                                ,radius
                                ,color = color
                                ,thick = thick
                                )
            
            if b_annotate:
                frame = draw_text(frame
                                 ,msg = str(_circleEnum)
                                 ,fontscale = 0.5
                                 ,color = convert_color(color)
                                 ,pos = self.annotatePointFromRect(rect)
                                 )
                

        for _rayObj in data.getListType('ray'):
                
            _rayEnum, _rayData = _rayObj
            
            if coordsRelative == 'origToMain':
                xy0 = tuple(self.scaleOrigToMain(x) for x in _rayData[0])
                xy1 = tuple(self.scaleOrigToMain(x) for x in _rayData[1])
            elif coordsRelative == 'origToZoom':
                xy0 = self.pointOrigToZoom(_rayData[0])
                xy1 = self.pointOrigToZoom(_rayData[1])
            elif coordsRelative == 'origToScore':
                xy0 = self.pointOrigToScore(_rayData[0])
                xy1 = self.pointOrigToScore(_rayData[1])
        
            frame = draw_ray(frame
                            ,xy0
                            ,xy1
                            ,color = color
                            ,thick = thick
                            #TODO - bOffsetRay so you can see the motion blur
                            )
            
            if b_annotate:
                frame = draw_text(frame
                                 ,msg = str(_rayEnum)
                                 ,fontscale = 0.5
                                 ,color = convert_color(color)
                                 ,pos = self.annotatePointFromRect(
                                            self.pointsToRelativeRect(xy0, xy1)
                                            )
                                 )

    def adjustOrient(self):
        ''' rotate images here, to apply minimal amount of coord adjustment.
            this is called immediately before show(), so all other processing
            in Display occurs on original orientation. Within show(), we convert
            selectRoi back into orig-orientation-coords. So, it's only going into
            new orientation for user-view (imshow) / user-write (selectRoi).
        '''
        if self.orientation != 0:
            
            self.frame = imutils.rotate_bound(self.frame
                                            ,self.orientation)

            if self.zoomOn and self.zoomFrame is not None:
                
                self.zoomFrame = imutils.rotate_bound(self.zoomFrame
                                                    ,self.orientation)

            if (self.scoreFrame is not None and 
                ((self.scoreOn and not(self.scoreOff)) or self.trackOn)):

                self.scoreFrame = imutils.rotate_bound(self.scoreFrame
                                                    ,self.orientation)



    def setTrack(self, roiTrack=None, circleTrack=None, trackScore=None):

        self.trackScore.load(trackScore)
        
        self.trackOn = False
        if self.trackScore.checkHasContents():
            if self.trackScore.checkHasValid():
                self.trackOn = True
    
    
    def drawTrackers(self):
        ''' Draw onto frame(s) based on data from trackFactory.
            All data is relative to Orig frame size; so we need to
            convert to Main or convert to Zoom where nec.
        '''
        
        if self.trackOn:
            
            self.drawOntoPane(frame = self.frame
                             ,data = self.trackScore
                             ,coordsRelative = 'origToMain'
                             ,color = 'red'
                             ,thick = 2
                             ,b_annotate = self.bAnnotateObjEnum
                             )

            if self.zoomOn and self.zoomRect is not None:

                self.drawOntoPane(frame = self.zoomFrame
                                ,data = self.trackScore
                                ,coordsRelative = 'origToZoom'
                                ,color = 'red'
                                ,thick = 1
                                ,b_annotate = False
                                )

            if (self.scoreOn and not(self.scoreOff) 
                and self.scoreRect is not None):

                self.drawOntoPane(frame = self.scoreFrame
                                ,data = self.trackScore
                                ,coordsRelative = 'origToScore'
                                ,color = 'red'
                                ,thick = 1
                                ,b_annotate = False
                                )


    def buildScoreFrame(self):
        ''' create a score_img (that gets attached to -> self.scoreFrame) based on scoreRect.
            this is a clone of buildZoomFrame()
        '''

        if self.scoreRect is None:
            
            score_img = np.zeros(self.frame.shape, dtype='uint8')
            score_img = draw_text(score_img, "n/a")
        
        else:
            
            score_img = crop_img( self.getOrigFrame()
                                  ,self.absRect(
                                    tuple( 
                                     self.scaleMainToOrig(p) for p in self.scoreRect
                                        )
                                    )
                                )
        
        widthZoom, heightZoom = self.widthZoomWindow,self.heightZoomWindow

        if self.scoreRect is not None:
            
            if any(map(lambda x: x < self.modZeroSize, 
                        self.rectMainToOrig(self.scoreRect)[2:4])):

                #still ensure mod0 in score window
                widthZoom = int( int(self.widthZoomWindow / self.scoreRect[2]) 
                                      * self.scoreRect[2])
        
        if score_img.shape[0] < 1 or score_img.shape[1] < 1:
            score_img = np.zeros(self.frame.shape)
            score_img = draw_text(score_img, "n/a")
        
        score_img  = resize_img(score_img, True, (widthZoom, heightZoom))

        return score_img
    
    
    def buildZoomFrame(self):
        ''' create a zoom_img (that gets attached to -> self.zoomFrame) based on zoomRect.
            we're concerned with modulo-zero resizes in here, when the zoomFrame is below
            a certain size.
        '''

        if self.zoomRect is None:
            
            #TODO - only create this once
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
        
        if zoom_img.shape[0] < 1 or zoom_img.shape[1] < 1:
            #sanity check / temporary hack. really shouldn't get here
            # self.zoomRect = None
            # return None
            zoom_img = np.zeros(self.frame.shape)
            zoom_img = draw_text(zoom_img, "n/a")
        
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

            if self.scoreOn and not(self.scoreOff):
                
                windowName = "score_display"
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
                #Bug- does this need rotate_bounds as below?
                self.zoomRect = rect
                self.zoomOn = True
                self.resetOperators()

            if self.cmdSelectRoiMain:
                
                self.frame = imutils.rotate_bound(self.frame, - self.orientation)
                _roiRect = self.rectMainToOrig(rect)
                
                if self.trackTypeEnum == 0:     

                    #circle
                    self.outputScore.addCircle( _roiRect
                                                ,self.trackObjEnum
                                              )

                elif self.trackTypeEnum == 1:   
                    
                    #ray
                    self.outputScore.addRayPoint(
                                         rayPoint = self.centerPointFromRect(_roiRect)
                                        ,rayPointEnum = 0
                                        ,objEnum = self.trackObjEnum
                                        )
                    
                    #to fix bug: otherwise it will be wrong view rotation on 2nd point select
                    self.frame = imutils.rotate_bound(self.frame, self.orientation)
                    
                    rect2 = cv2.selectROI(windowName, self.frame, True, False )
                    rect2 = self.adjOrientationRect(rect2, self.frame.shape[:2][::-1])
                    
                    #to fix bug: otherwise it will be wrong view rotation on 2nd point select
                    self.frame = imutils.rotate_bound(self.frame, -self.orientation)

                    _roiRect2 = self.rectMainToOrig(rect2)

                    self.outputScore.addRayPoint(
                                         rayPoint = self.centerPointFromRect(_roiRect2)
                                        ,rayPointEnum = 1
                                        ,objEnum = self.trackObjEnum
                                        )
                
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
            
            _roiRect = self.rectZoomToOrig(rect)

            if self.trackTypeEnum == 0:     

                #circle
                self.outputScore.addCircle( _roiRect
                                            ,self.trackObjEnum
                                            )

            elif self.trackTypeEnum == 1:   
                
                #ray
                self.outputScore.addRayPoint(
                                     rayPoint = self.centerPointFromRect(_roiRect)
                                    ,rayPointEnum = 0
                                    ,objEnum = self.trackObjEnum
                                    )
                
                #to fix bug: otherwise it will be wrong view rotation on 2nd point select
                self.frame = imutils.rotate_bound(self.frame, self.orientation)
                self.zoomFrame = imutils.rotate_bound(self.zoomFrame, self.orientation)
                
                rect2 = cv2.selectROI(windowName, self.zoomFrame, True, False )

                rect2 = self.adjOrientationRect(rect2, self.zoomFrame.shape[:2][::-1])

                #to fix bug: otherwise it will be wrong view rotation on 2nd point select
                self.frame = imutils.rotate_bound(self.frame, -self.orientation)
                self.zoomFrame = imutils.rotate_bound(self.zoomFrame, -self.orientation)
                
                _roiRect2 = self.rectZoomToOrig(rect2)

                self.outputScore.addRayPoint(
                                     rayPoint = self.centerPointFromRect(_roiRect2)
                                    ,rayPointEnum = 1
                                    ,objEnum = self.trackObjEnum
                                    )
                                    
            self.roiSelected = True
            self.resetOperators()

            # we don't need to ensure modulo-zero here, that has already been 
            # enforced (or not) in the choice of zoomFrame-width in buildZoomFrame()

        if (self.windowThree and 
            ((self.scoreOn and not(self.scoreOff) and self.bShowScoring)
            or self.trackOn)):

            windowName = 'score_display'
            if self.orientation in (90,270): windowName += "_profile"    

            cv2.imshow(windowName, self.scoreFrame)
            key3 = cv2.waitKey(1) & 0xFF

        #new func -----------
        if key == ord("s"):
            initBB = cv2.selectROI("img_display", self.frame, True, False )

        if self.zoomOn and self.zoomFrame is not None and self.windowTwo:
            pass
            #TODO - key2 only if windowTwo is shown
            #TODO - add key3
            # if key2 == ord('z'):

            #     self.zoomRect = self.zoomInRect(copy.copy(self.zoomRect))
                
            #     self.resetOperators()
                

            # if key2 == ord('x'):

            #     self.zoomRect = self.zoomInRect(copy.copy(self.zoomRect)
            #                                     ,b_zoomout=True)
            #     self.resetOperators()
                
    # test helpers --------------------
    # use these only for test stubs

    def _test_set_outputScore(self, outputScore):

        self.outputScore = outputScore

    
    # main helpers ---------------------
    # converting coords and shapes b/w orig, main, zoom, score windows

    def roiToMain(self, input_rect):
        ''' return relative-rect roi relative to main-window coord's.
                (since there's no cropping, we only stretch.)
                (we expect the stretch to be modulo-zero as 
                 640 1280 1920 are multiple )
        '''
        rect = copy.copy(input_rect)

        rectMain = tuple(map(self.scaleOrigToMain, rect))
        
        return rectMain

    def roiToZoom(self, input_rect):
        ''' return a relative-rect roi relative to zoom-window coord's.
                (there's cropping and stretching.)
                (we don't assume it is modulo-zero; but if it is, 
                 this function should preserve that.)
        '''
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

    def roiToScore(self, input_rect):
        ''' return a relative-rect roi relative to score-window coord's.
                (there's cropping and stretching.)
                (we don't assume it is modulo-zero; but if it is, 
                 this function should preserve that.)
        '''
        rect = copy.copy(input_rect)
        
        #orig->main
        x0, y0, dx, dy = map(self.scaleOrigToMain, rect)  
        
        #main->zoom
        x0,y0 = self.coordMainToScore((x0,y0))
        x0 = self.scaleMainToScore(x0)
        y0 = self.scaleMainToScore(y0)
        dx = self.scaleMainToScore(dx)
        dy = self.scaleMainToScore(dy)

        rectScore = (x0, y0, dx, dy)
        
        return rectScore

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

        # zoomFct = 0.1
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
        
        x = coord_xy[0] - self.zoomRect[0]
        y = coord_xy[1] - self.zoomRect[1]

        return x,y

    def coordMainToScore(self, coord_xy):
        ''' convert the coord (a tuple of integers) in main window 
            to the coord in zoom window '''
        
        x = coord_xy[0] - self.scoreRect[0]
        y = coord_xy[1] - self.scoreRect[1]

        return x,y

    def coordZoomToMain(self, coord_xy):
        ''' convert the coord (a tuple of integers) in zoom window 
            to the coord in main window '''
        
        x = coord_xy[0] + self.zoomRect[0]
        y = coord_xy[1] + self.zoomRect[1]

        return x,y

    def pointOrigToZoom(self, xy):
        ''' given point in coords-relative-to-rect, return point relative-to-zoom'''
        _xy = tuple(self.scaleOrigToMain(x) for x in xy)
        _xy = tuple(map(int, self.coordMainToZoom(_xy)))
        _xy = tuple(self.scaleMainToZoom(x) for x in _xy)
        return _xy
    
    def pointOrigToScore(self, xy):
        ''' given point in coords-relative-to-rect, return point relative-to-score'''
        _xy = tuple(self.scaleOrigToMain(x) for x in xy)
        _xy = tuple(map(int, self.coordMainToScore(_xy)))
        _xy = tuple(self.scaleMainToScore(x) for x in _xy)
        return _xy

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

    def scaleMainToScore(self, val):
        ''' a stretch transform: does rounding nearest for non modulo-zero '''
        adj_factor = float(self.scoreFrame.shape[1]) / float(self.scoreRect[2])
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

    @staticmethod
    def circleToRect(input_circle):
        ''' takes x,y, radius, fits to enclosing relative-format rect
            (x,y, radius)  -> (x0,y0, d_x, d_y) 
        '''

        x, y, radius = copy.copy(input_circle)            

        x0 = int(x - radius)
        y0 = int(y - radius)
        dx = int(2 * radius)
        dy = int(2 * radius)

        return (x0, y0, dx, dy)

    @staticmethod
    def centerPointFromRect(input_rect):
        ''' takes:   relative-format rect (x,y,dx,dy )
            returns: (x1,y1)
        '''

        x, y, dx, dy = copy.copy(input_rect)            

        return (x + int(dx / 2), y + int(dy / 2))

    @staticmethod
    def annotatePointFromRect(input_rect, offset = 20):
        ''' takes:   relative-format rect (x,y,dx,dy )
            returns: (x,y)
        '''

        x, y, dx, dy = copy.copy(input_rect)

        x_return = int(x + int(dx / 2))
        y_return = y - offset

        if y_return < 0:
            #this will insure no OOB error
            return self.centerPointFromRect(input_rect)
        else:
            return (x_return, y_return)
        

    @staticmethod
    def pointsToRelativeRect(point0, point1):
        ''' takes two tuples of int's: point0 (x0,y0), point1 (x1, y1)
            returns (x,y, dx, dy)
            note: point0, point1 are not nec. in order
        '''

        x = min(point0[0], point1[0])
        y = min(point0[1], point1[1])
        dx = max(point0[0], point1[0]) - x
        dy = max(point0[1], point1[1]) - y

        #minDims(min_scalar_width = 1)

        return (x, y, dx, dy)

    @staticmethod
    def minDimsForRect(  input_rect
                        ,output_bounds
                        ,min_scalar_width = 1
                        ,max_multiple_width = 5
                        ):
        ''' returns: relative-format-rect with potentially expanded dimensions.
                     (used for better viewing in score_display.
                      output_bounds allow us to not go out of index)
            input_rect: (x,y, dx, dy)
            output_bounds: (h,w) tuple
            min_scalar_width: int or None; if None, don't process this condition
            max_multiple_width: int or None; if None, don't process this condition
        '''

        #set inputs
        b_scalar = False if (min_scalar_width is not None) else True
        b_multiple = False if (max_multiple_width is not None) else True

        x, y, dx, dy = copy.copy(input_rect)
        h, w = output_bounds

        #check conditions
        if not(b_scalar):
            if ((dx > min_scalar_width) and
                (dy > min_scalar_width)):
                b_scalar = True
        
        if not(b_multiple):
            if ((dy*max_multiple_width > dx) and
                (dx*max_multiple_width > dy)):
                b_multiple = True

        #early return
        if b_scalar and b_multiple:
            return input_rect

        #find needed expansion to satisfy condition
        if not(b_scalar):
            
            x_expand_s = max(min_scalar_width - dx, 0)
            y_expand_s = max(min_scalar_width - dy, 0)

            x_delta_s = round(x_expand_s / 2, 0)
            y_delta_s = round(y_expand_s / 2, 0)

        else:
            x_expand_s, y_expand_s = 0, 0
            x_delta_s, y_delta_s = 0, 0

        if not(b_multiple):
            
            x_expand_m = max(int((dy / max_multiple_width) - dx), 0)
            y_expand_m = max(int((dx / max_multiple_width) - dy), 0)

            x_delta_m = round(x_expand_m / 2, 0)
            y_delta_m = round(y_expand_m / 2, 0)

        else:
            x_expand_m, y_expand_m = 0, 0
            x_delta_m, y_delta_m = 0, 0

        x_expand = max(x_expand_s, x_expand_m)
        y_expand = max(y_expand_s, y_expand_m)

        x_delta = max(x_delta_m, x_delta_s)
        y_delta = max(y_delta_m, y_delta_s)

        
        #do expansion                
        if x_delta > 0:
        
            x_diff = [el[0] + el[1] for el in zip([x, x+dx], [-x_delta, x_delta])]
            
            x_diff[0] = max(0, x_diff[0])
            x_diff[1] = min(w, x_diff[1])

            #remainder
            x_delta_2 = max(0, x_expand - ((x_diff[1] - x_diff[0]) - dx))
            
            if x_delta_2 > 0:
                
                ind = 1 if ((x - x_delta) < x_diff[0]) else 0
                
                new_val = (x_diff[ind] +
                            ([-1,1][ind] * x_delta_2)
                            )
                                        
                if ind == 0:
                    new_val = max(new_val, 0)
                elif ind == 1:
                    new_val = min(new_val, w)

                x_diff[ind] = new_val

            #modify output
            x, dx = x_diff[0], x_diff[1] - x_diff[0]

        if y_delta > 0:

            y_diff = [el[0] + el[1] for el in zip([y, y+dy], [-y_delta, y_delta])]
            
            y_diff[0] = max(0, y_diff[0])
            y_diff[1] = min(h, y_diff[1])

            #remainder
            y_delta_2 = max(0, y_expand - ((y_diff[1] - y_diff[0]) - dy))
            
            if y_delta_2 > 0:
                
                ind = 1 if ((y - y_delta) < y_diff[0]) else 0
                
                new_val = (y_diff[ind] +
                            ([-1,1][ind] * y_delta_2)
                            )
                                        
                if ind == 0:
                    new_val = max(new_val, 0)
                elif ind == 1:
                    new_val = min(new_val, h)

                y_diff[ind] = new_val

            #modify output
            y, dy = y_diff[0], y_diff[1] - y_diff[0]


        #clean and return
        modified_rect = (x, y, dx, dy)
        modified_rect = map(int, modified_rect)
        
        return tuple(modified_rect)

    