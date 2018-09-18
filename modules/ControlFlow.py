import os, sys, time
import numpy as np
import cv2
import argparse
# from modules import GlobalsC as g

class FrameFactory:

    def __init__(self):
        self.play = False
        self.advanceFrame = False
        self.frames = []
        self.cam = None
        self.pauseTime = 0

    def setCam(self, cam):
        self.cam = cam

    def preload(self):
        
        ret, frame = self.cam.read()

        if ret:
            self.frames.append(frame)
        else:
            return

    def setPlay(self, playOn):
        self.playOn = playOn

    def setAdvanceFrame(self, advanceFrame):
        self.advanceFrame = advanceFrame
        

    def queryNewFrame(self):
        if self.playOn or self.advanceFrame:
            return True
        return False