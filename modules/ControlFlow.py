import os, sys, time
import numpy as np
import cv2
import argparse
# from modules import GlobalsC as g

class FrameFactory:

    def __init__(self):
        self.play = False
        self.advanceFrame = False
        self.retreatFrame = False
        self.preloaded = False
        self.frames = []
        self.cam = None
        self.gui = None
        self.pauseTime = 0
        self.frameCounter = 0

    def setCam(self, vidPathFn):
        self.cam = cv2.VideoCapture(vidPathFn)

    def preload(self):

        try:
            while(self.cam.isOpened()):
                
                ret, frame = self.cam.read()

                if ret:
                    self.frames.append(frame)
                else:
                    break

            if len(self.frames) > 0:
                self.preloaded = True

        except:
            return 


    def isOpened(self):
        
        if self.preloaded:
        
            if self.frameCounter > len(self.frames) - 1:
        
                if self.playOn:
                    self.cam.release()
                    return False
                else:
                    return True
            else:
                return True
        else:
            return self.cam.isOpened()


    def getFrame(self):
        if self.preloaded:
            
            if len(self.frames) - 1 < self.frameCounter:
                return False, None
            
            return True, self.frames[self.frameCounter]
            
        else:
            ret, frame = self.cam.read()
            if not(ret):
                self.cam.release()
            return ret, frame

    
    def setPlay(self, playOn):
        self.playOn = playOn

    def setAdvanceFrame(self, advanceFrame):
        self.advanceFrame = advanceFrame

    def setRetreatFrame(self, retreatFrame):
        self.retreatFrame = retreatFrame

    
    def deltaCounter(self, requestAmt, bypassValidation=False):
        
        if self.preloaded:
            
            if bypassValidation:
                self.frameCounter += requestAmt
                return True
            
            newCounter = requestAmt + self.frameCounter
            
            if (newCounter <= len(self.frames) - 1 and newCounter >= 0):
                self.frameCounter += requestAmt
                return True
            else:
                return False
        else:
            if requestAmt == 1:
                self.frameCounter += requestAmt
                return True
            else:
                return False

    
    def queryNewFrame(self):
        
        if self.playOn:
            return self.deltaCounter(1, bypassValidation=True)
        
        if self.advanceFrame:
            self.advanceFrame = False
            return self.deltaCounter(1)
            
        if self.retreatFrame:
            self.retreatFrame = False
            return self.deltaCounter(-1)
            
        return False

    def linkGui(self, objGui):
        self.gui = objGui

    def updateGui(self, vidFn="", cumTimeArray=None):
        ''' call after getFrame() for correct data on frameCounter'''        
        
        if self.gui is None: return

        self.gui.myGui.set_sv_vidFn(vidFn)
        self.gui.myGui.set_sv_frameI(str(self.frameCounter))
        
        if cumTimeArray is not None:
            self.gui.myGui.set_sv_cumTime(str(cumTimeArray[self.frameCounter]))

