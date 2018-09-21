import os, sys, time, copy
import numpy as np
import cv2
import argparse
from modules.Utils import TimeLog
from modules import GlobalsC as g

class FrameFactory:

    ''' Manage frames from an open VideoCapture(file) object or preloaded list:
        - manipulate/validate frameCounter
        - validate video begin/end; suggest break from this frameloop       
    '''

    def __init__(self):
        self.play = False
        self.advanceFrame = False
        self.retreatFrame = False
        self.rewindCmd = False
        self.fastforwardCmd = False
        self.preloaded = False
        self.frames = []
        self.cam = None
        self.frameCounter = -1
        self.firstN = 0
        self.failedLoad = False


    def setCam(self, vidPathFn):
        self.cam = cv2.VideoCapture(vidPathFn)
        
        #TODO - raise opencv warning
        if not(self.cam.isOpened()):
            self.failedLoad = True

    def setFirstN(self, firstN):
        self.firstN = firstN

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
        
        if self.firstN > 0:
            if self.frameCounter > self.firstN:
                return False
        
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

    def getFrameTotal(self):
        if self.frames is None:
            return -1
        return len(self.frames) - 1

    def setPlay(self, playOn):
        self.playOn = playOn

    def setAdvanceFrame(self, advanceFrame):
        self.advanceFrame = advanceFrame
        g.switchAdvanceFrame = False

    def setRetreatFrame(self, retreatFrame):
        self.retreatFrame = retreatFrame
        g.switchRetreatFrame = False

    def setRewind(self, rewind):
        self.rewindCmd = rewind
        g.switchRewind = False

    def setFastforward(self, fastforward):
        self.fastforwardCmd = fastforward
        g.switchFastforward = False


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

        if self.rewindCmd:
            self.rewindCmd = False
            return self.deltaCounter(-10)

        if self.fastforwardCmd:
            self.fastforwardCmd = False
            return self.deltaCounter(10)
            
        return False

    def getFailedLoad(self):
        return self.failedLoad


class TimeFactory:

    ''' Track frametime-log's sync with FrameFactory and video-display-time. '''
    
    def __init__(self):
        self.b_delay = False
        self.t_0 = 0
        self.pauseT0 = 0
        self.pauseTime = 0
        self.play = True
        self.cumtime = None
        self.frameCurrent = 0
        self.delaySecs = 0.0
        self.avgFps = 0.0
        self.avgFrametime = 0.0

    def setFrametimeLog(self, logPathFn):
        try:
            self.cumtime = TimeLog().get_cum_time(logPathFn) #[1:]
        except:
            self.cumtime = None

        try:
            self.avgFps = TimeLog().get_avg_frametime(logPathFn, b_hz=True)
            self.avgFrametime = TimeLog().get_avg_frametime(logPathFn, b_hz=False)
        except:
            self.avgFps = None
            self.avgFrametime = None


    def setDelay(self, b_delay):
        self.b_delay = b_delay

    def setDelaySecs(self, delaySecs):
        self.delaySecs = float(delaySecs)

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

    def avgFrameFps(self):
        return (self.avgFps, self.avgFrametime)

    def lagTuple(self):
        
        if not(self._validCumTime()) or not(self._validCurrentFrame()):
            return (-1, -1)
        
        _lag0 = -1 if (self.frameCurrent < 1) else 0
        _lag1 = -1 if (self.frameCurrent > len(self.cumtime) - 2) else 0
        
        if _lag0 != -1:
            _lag0 = self.cumtime[self.frameCurrent] - self.cumtime[self.frameCurrent - 1]
        if _lag1 != -1:
            _lag1 = self.cumtime[self.frameCurrent + 1] - self.cumtime[self.frameCurrent]        
        
        return (_lag0, _lag1)
        

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
        
        if self.delaySecs > 0.001:
            time.sleep(self.delaySecs)
            return

        secsAhead = ( self.cumtime[self.frameCurrent] 
                        - 
                      (time.time() - (self.pauseTime + self.t_0))
                    )

        if secsAhead > 0.001:
            time.sleep(secsAhead - 0.001)

        return 
        
class DirectoryFactory:

    ''' Handle directory path and video-file selection and rotation'''

    def __init__(self):
        self.playCounter = 0
        self.b_play_dir = False
        self.initDir = ""
        self.fn = ""
        self.listVids = None

    def setRunType(self, b_play_dir = False):
        self.b_play_dir = b_play_dir

    def setData(self, initDir, fn=""):
        
        self.initDir = initDir

        if not(self.b_play_dir):
            self.fn = fn
        
        if self.b_play_dir:

            vidExts = (".avi",)
            
            listFiles = os.listdir(self.initDir)
            
            self.listVids = filter(lambda fn: 
                                    any([ext in fn for ext in vidExts])
                                  ,listFiles)

    def vidFn(self):

        if self.b_play_dir:
            if len(self.listVids) == 0:
                vidFn = ""
            else:
                vidFn = self.listVids[self.playCounter % len(self.listVids)]
        else:
            vidFn = self.fn
        
        return vidFn
    
    def vidPathFn(self):

        vidFn = self.vidFn()

        return os.path.join(self.initDir, vidFn)

    def frametimePathFn(self):

        _vidFn = self.vidFn()
        _frametimeFn = _vidFn.split(".")[0]
        _frametimeFn += ".txt"
        
        return os.path.join(self.initDir, _frametimeFn)

    def checkExit(self, bFailedLoad):
        ''' return True to exit from outermost loop; exit program'''        

        if bFailedLoad:
            if not(self.b_play_dir):
                print 'Exiting: video file not able to be opened.'
                return True
        
        if self.b_play_dir:
            if len(self.listVids) < 1:
                print 'Exiting: failed to find video files in this directory'
                return True
        
        return False

    def incrementPlayCounter(self):
        self.playCounter += 1

