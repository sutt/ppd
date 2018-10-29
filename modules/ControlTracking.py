import os, sys, time, copy, json, re, argparse

import numpy as np
import cv2

sys.path.append("../")
from vidwriter import VidWriter
from miscutils import uniqueFn

from modules.Utils import TimeLog
from modules.Utils import MetaDataLog

from modules.ImgUtils import (crop_img, filter_pixels_circle
                             ,pixlist_to_pseduoimg)
from modules.ImgProcs import (threshA, transformA, repairA)
from modules.TrackA import (find_xy, find_radius)

from modules.IterThresh import iterThreshA

from modules.DataSchemas import ScoreSchema

from modules import GlobalsC as g

class TrackFactory:

    ''' handles tracking processing and tracking-stored-data '''
    
    def __init__(self, on=False):
        self.on = on
        self.currentFrame = None
        self.currentFrameInd = -1
        
        self.trackingOnPrevious = None
        self.bTrackingOnChange = False

        self.currentTrackSuccess = False
        self.currentTrackScore = ScoreSchema()

        self.threshInitial = [ (0,0,0), (255,255,255) ]

        self.declaredBallColor = ""

        self.bPerformTrainOnNewData = False
        self.trainingData = []
        self.trainingThreshes = []

        self.bTrackTimer = False
        self.trackTimerData = {}

        self.savedParams = None

        # tp_: tracking parameters
        self.tp_tracking_blur = 1
        self.tp_repair_iterations = 1
        self.tp_b_hsv = False

        # TrackingAlgo class inherits TrackingTemplate 
        # and is instantiated here?

    def setInit(self, ballColor = ""):
        self.declaredBallColor = ballColor
        
        if self.declaredBallColor == "green":
            self.threshInitial = [ (29, 86, 6), (64, 255, 255) ]

        if self.declaredBallColor == "orange":
            self.threshInitial = [ (0, 96, 192), (88, 232, 255) ]
            
        # From old notes:
        # rgb: (orange ball) [  0  96 192] [ 88 232 255]
        # green sharpie:  [ 15 106  86] [ 81 171 148]

    def setCmd( self 
               ,trackingOn 
               ,outputParams=None
               ,alterParams=None
               ,resetParams=None
               ):
        
        self.on = trackingOn
                
        # this is for forcing a display "redraw" when track toggles On/Off
        if self.trackingOnPrevious is not None:
            if trackingOn != self.trackingOnPrevious:
                self.bTrackingOnChange = True
            else:
                self.bTrackingOnChange = False
        self.trackingOnPrevious = trackingOn

        
        if outputParams is not None:
            if outputParams:
                self.outputParams()
                g.switchOutputParams = False

        if alterParams is not None:
            if alterParams:
                self.saveParams()
                self.alterParams()
                g.switchAlterParams = False
                self.bTrackingOnChange = True

        if resetParams is not None:
            if resetParams:
                self.restParams()
                g.switchResetParams = False
                self.bTrackingOnChange = True

    def outputParams(self):
        try:
            with open("notes/tracking_params.json", "w") as f:
                json.dump(self.getTrackParams(), f, indent = 4)
        except:
            print 'failed to output tracking params'

    def alterParams(self):
        try:
            with open("notes/tracking_params.json", "r") as f:
                d_params = json.load(f)
        except Exception as e:
            print 'failed to read in json'
            print e.message

        try:
            self.setTrackParams(**d_params)
        except Exception as e:
            print 'failed to set track params from json'
            print e

    def saveParams(self):
        self.savedParams = self.getTrackParams()

    def restParams(self):
        self.setTrackParams(**self.savedParams)

    def resetTracker(self):
        self.trackTimerData = {}

    def getTrackOnChange(self):
        ''' return True to make a pass thru inner loop of guiview
            only updating state related to tracking. This allows us to make
            changes immediately apparent in Display'''

        if self.bTrackingOnChange is None:
            return False
        else:
            return self.bTrackingOnChange

    def getTrackScore(self):
        if not(self.on): return None
        return self.currentTrackScore.getAll()

    def setFrameInd(self, frameInd):
        self.currentFrameInd = frameInd
    
    def setFrame(self, currentFrame):
        if not(self.on): return
        self.currentFrame = currentFrame

    def setFrameScore(self, frameScoreData):
        
        if not(self.on): return

        if frameScoreData is None: return
        if len(frameScoreData) != 2: return
        
        frameType, frameScore = frameScoreData

        #TODO-SS
        objScoring = ScoreSchema()
        objScoring.load(frameScore)
        circleDataObj0 = objScoring.getData(objEnum=0)

        if frameType == "training":
            
            datum = self.buildTrainingDatum(circleDataObj0, self.currentFrame)
            
            if datum is not None:
                self.trainingData.append(datum)

                if self.bPerformTrainOnNewData:
                    self.trainProc()
            

        if frameType == "scoring":
            pass
            #do evaluation

    @classmethod
    def buildTrainingDatum(cls, cropRect, img):
        
        if cropRect is None or img is None:
            return None

        try:
            datum = {}
            datum['cropRect'] = cropRect
            datum['cropImg'] = crop_img(img.copy(), cls.absRect(cropRect))
            return datum
        except:
            return None

    def trainProc(self):
        ''' take training data and build thresh hi/lo from them '''
        
        if len(self.trainingData) < 1: return

        # only run iterthresh on latest img
        img = self.trainingData[len(self.trainingData) - 1].get('cropImg', None)

        if img is None: return
        if img.shape[0] < 1 or img.shape[1] < 1: return

        circle_img = pixlist_to_pseduoimg(
                            filter_pixels_circle(img)
                            )

        out_thresh = iterThreshA( circle_img
                                 ,goal_pct = .95
                                 ,steep = False)

        _lo , _hi = out_thresh[1][3], out_thresh[1][4]
        
        self.trainingThreshes.append((_lo, _hi))
        
        self.combine_threshes(self.trainingThreshes)
        
        self.threshInitial = (tuple(map(int, _lo)), tuple(map(int,_hi)))
        

    def setTrackTimer(self, bTrackTimer):
        if isinstance(bTrackTimer, bool):
            self.bTrackTimer = bTrackTimer

    def getTrackTimerData(self):
        return self.trackTimerData

    def getTrackTimerDataCurrent(self):
        return self.trackTimerData.get(self.currentFrameInd - 1, -1)


    def setTrackParams( self
                        ,tracking_blur=None
                        ,repair_iterations=None
                        ,thresh_lo=None
                        ,thresh_hi=None
                        ):
        
        if tracking_blur is not None:
            self.tp_tracking_blur = tracking_blur

        if repair_iterations is not None:
            self.tp_repair_iterations = repair_iterations

        if thresh_lo is not None:
            self.threshInitial[0] = tuple(thresh_lo)

        if thresh_hi is not None:
            self.threshInitial[1] = tuple(thresh_hi)

    
    def getTrackParams(self):
        
        params = {}

        params['tracking_blur'] = self.tp_tracking_blur
        params['repair_iterations'] = self.tp_repair_iterations
        params['thresh_lo'] = self.threshInitial[0]
        params['thresh_hi'] = self.threshInitial[1]

        return params

    
    def trackFrame(self):

        if not(self.on): return

        tracking_blur = self.tp_tracking_blur
        repair_iterations = self.tp_repair_iterations 

        thresh_lo = self.threshInitial[0]
        thresh_hi = self.threshInitial[1]

        if self.bTrackTimer:
            t0 = time.time()

        img_t = transformA(self.currentFrame.copy(), tracking_blur)
        
        img_mask = threshA(  img_t 
                            ,threshLo = thresh_lo   
                            ,threshHi = thresh_hi ) 

        if not(img_mask is None):

            img_mask = repairA(img_mask, iterations = repair_iterations)

            x,y = find_xy(img_mask)
            radius = find_radius(img_mask)
                    
            if radius > 0:
                self.currentTrackSuccess = True

            self.currentTrackScore.addCircle(
                                     self.circleToRect((x,y,radius))
                                    ,objEnum=0   #TODO-SS
                                    )

        if self.bTrackTimer:
            if self.currentFrameInd not in self.trackTimerData.keys():
                t_proc = time.time() - t0
                self.trackTimerData[self.currentFrameInd] = t_proc





    # helper functions ------

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
    def combine_threshes(data, liberal = True ):
        ''' data is a list of (lo, hi) 3-ple's; find the union '''
        
        if len(data) < 1:
            return ( np.array( [0,0,0], dtype = 'uint8' ),
                     np.array( [255,255,255], dtype = 'uint8' ) )
        
        _lo, _hi = [[255,255,255], [0,0,0]]

        for row in data:
            
            lo, hi = row[0], row[1]
        
            for i,clr in enumerate(lo):
                if clr < _lo[i]: 
                    _lo[i] = clr
        
            for i,clr in enumerate(hi):
                if clr > _hi[i]: 
                    _hi[i] = clr
        
        return ( np.array( _lo, dtype = 'uint8') 
                ,np.array( _hi, dtype = 'uint8') )



if __name__ == "__main__":

    sys.path.append("../")
    from modules.ControlDisplay import Display
    
    cam = cv2.VideoCapture("../data/proc/hello-training-data/output4.avi")
    ret, frame = cam.read()
    
    display = Display()

    trackFactory = TrackFactory(on=True)

    display.setFrame(frame)
    
    trackFactory.setInit(ballColor="green")
    trackFactory.setFrame(frame)
    trackFactory.trackFrame()
    
    roi = trackFactory.getCurrentTrackRoi()
    if roi is not None:
        roi = (int(roi[0]) - 20, int(roi[1]) - 20,  40,  40)
        print roi

    circle = trackFactory.getCurrentTrackCircle()
    print circle
    
    display.setTrack(roiTrack = roi, circleTrack=circle)
    display.drawTrackers()
    
    while(True):
        display.show()
