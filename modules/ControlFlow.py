import os, sys, time
import numpy as np
import cv2
import argparse
# from modules import GlobalsC as g

class FrameFactory:

    def __init__(self):
        self.play = False
        self.advanceFrame = False
        self.preloaded = False
        self.frames = []
        self.cam = None
        self.pauseTime = 0

    def setCam(self, cam):
        self.cam = cam

    def preload(self):

        try:
            while(cam.isOpened()):
                
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
            return True
        else:
            return self.cam.isOpened()

    def getFrame(self):
        if self.preloaded:
            #TODO - check frames list length
            # return self.frames[frameCounter]
            print 'here'
            return False
        else:
            return self.cam.read()

    
    def setPlay(self, playOn):
        self.playOn = playOn

    def setAdvanceFrame(self, advanceFrame):
        self.advanceFrame = advanceFrame


    def queryNewFrame(self):
        
        if self.playOn:
            return True
        
        if self.advanceFrame:
            self.advanceFrame = False
            return True

        return False