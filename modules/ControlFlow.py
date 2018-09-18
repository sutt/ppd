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
        self.pauseTime = 0
        self.frameCounter = 0

    def setCam(self, vidPathFn):
        self.cam = cv2.VideoCapture(vidPathFn)

    # def setCam(self, cam):
    #     self.cam = cam

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
                print 'preloaded %s' % str(self.preloaded)

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


    def queryNewFrame(self):
        
        if self.playOn:
            self.frameCounter += 1  #TODO make this expectedFrame vs actualFrame
            return True
        
        if self.advanceFrame:
            self.advanceFrame = False
            self.frameCounter += 1
            return True

        if self.retreatFrame:
            self.retreatFrame = False
            self.frameCounter -= 1
            return True

        return False