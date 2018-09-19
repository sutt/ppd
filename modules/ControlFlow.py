import os, sys, time, copy
import numpy as np
import cv2
import argparse
from modules.Utils import TimeLog
from modules import GlobalsC as g

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

    def getFrameCounter(self):
        return self.frameCounter

    def setPlay(self, playOn):
        self.playOn = playOn

    def setAdvanceFrame(self, advanceFrame):
        self.advanceFrame = advanceFrame
        g.switchAdvanceFrame = False

    def setRetreatFrame(self, retreatFrame):
        self.retreatFrame = retreatFrame
        g.switchRetreatFrame = False

    
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

    def updateGui(self, vidFn="", cumTimeCurrent=None, cumTimeTotal=None):
        ''' call after getFrame() for correct data on frameCounter'''        
        
        if self.gui is None: return

        self.gui.myGui.set_sv_vidFn(vidFn)
        self.gui.myGui.set_sv_frameI(str(self.frameCounter))
        
        _n = len(self.frames) - 1 if self.preloaded else "?"
        self.gui.myGui.set_sv_frameN(str(_n))
        
        if cumTimeCurrent is not None:
            self.gui.myGui.set_sv_cumTime(str(cumTimeCurrent))

        if cumTimeTotal is not None:
            self.gui.myGui.set_sv_cumTotal(cumTimeTotal)


class TimeFactory:

    def __init__(self):
        self.b_delay = False
        self.t_0 = 0
        self.pauseT0 = 0
        self.pauseTime = 0
        self.play = True
        self.cumtime = None
        self.frameCurrent = 0

    def setFrametimeLog(self, logPathFn):
        try:
            self.cumtime = TimeLog().get_cum_time(logPathFn) #[1:]
        except:
            self.cumtime = None

    def setDelay(self, b_delay):
        self.b_delay = b_delay

    def setT0(self):
        self.t_0 = time.time()
    
    def setFrameCurrent(self, frameCurrent):
        self.frameCurrent = frameCurrent

    def getCumFrametimeArray(self):
        return copy.copy(self.cumtime)

    def _validCumTime(self):
        if self.cumtime is None:
            return False
        if len(self.cumtime) == 0:
            return False
        return True

    def _validCurrentFrame(self):
        if self.frameCurrent < 0:
            return False
        if self.frameCurrent >= len(self.cumtime):
            return False
        return True

    def cumTimeCurrent(self):
        if not(self._validCumTime()):
            return -1
        if not(self._validCurrentFrame()):
            return -1
        return self.cumtime[self.frameCurrent]

    def cumTimeTotal(self):
        if not(self._validCumTime()): 
            return -1
        return self.cumtime[len(self.cumtime) - 1]

    def setPlay(self, playOn):
        if self.play == playOn: 
            return
        else:
            if playOn == False:
                self.pauseT0 = time.time()
            if playOn == True:
                self.pauseTime += (time.time() - self.pauseT0)
            self.play = playOn


    def delayFrame(self):
        ''' sleep in frame loop to match cumtime '''
        
        if not(self.b_delay): return

        if not(self.play): return
        
        if not(self._validCumTime()): return
        if not(self._validCurrentFrame()): return
        
        
        secsAhead = ( self.cumtime[self.frameCurrent] 
                        - 
                      (time.time() - (self.pauseTime + self.t_0))
                    )

        if secsAhead > 0.001:
            time.sleep(secsAhead - 0.001)

        return 
        
