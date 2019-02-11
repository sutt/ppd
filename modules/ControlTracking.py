import os, sys, time, copy, json, re, argparse

from collections import OrderedDict

import numpy as np
import cv2

sys.path.append("../")
from vidwriter import VidWriter
from miscutils import uniqueFn

from modules.Utils import TimeLog
from modules.Utils import MetaDataLog

from modules.ImgUtils import (crop_img, filter_pixels_circle
                             ,pixlist_to_pseduoimg)
from modules.ImgProcs import (threshA, transformA, repairA, threshMultiOr)
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

        self.threshes = []

        self.declaredBallColor = ""

        self.bPerformTrainOnNewData = False
        self.trainingData = []
        self.trainingThreshes = []

        self.bTrackTimer = False
        self.trackTimerData = {}

        self.savedParams = None

        # tp_: tracking parameters
        self.tp_trackAlgoEnum = 0
        self.tp_tracking_blur = 1
        self.tp_repair_iterations = 1
        self.tp_b_hsv = False

        # TrackingAlgo class inherits TrackingTemplate 
        # and is instantiated here?

    def setInit(self, ballColor = ""):
        self.declaredBallColor = ballColor
        
        if self.declaredBallColor == "green":
            self.threshInitial = [ (29, 86, 6), (64, 255, 255) ]

            self.threshes.append(tuple(self.threshInitial))
            self.threshes.append(((20, 60, 6),(40, 255, 255)))

        if self.declaredBallColor == "orange":

            thresh1 = ((6, 30, 120), (64, 255, 255))
            thresh2 = ((64, 100, 180), (90, 255, 255))
            thresh3 = ((90, 120, 200), (120, 255, 255))
            
            self.threshInitial = thresh1

            self.threshes = [thresh1, thresh2, thresh3]


    def setAlgoEnum(self, algoEnum):
        self.tp_trackAlgoEnum = algoEnum

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

        #TODO - update self.threshes, if necessary
        

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
                        ,threshes=None
                        ):
        
        if tracking_blur is not None:
            self.tp_tracking_blur = tracking_blur

        if repair_iterations is not None:
            self.tp_repair_iterations = repair_iterations

        if thresh_lo is not None:
            self.threshInitial[0] = tuple(thresh_lo)

        if thresh_hi is not None:
            self.threshInitial[1] = tuple(thresh_hi)

        if threshes is not None:
            self.threshes = copy.copy(threshes)

    
    def getTrackParams(self):
        
        params = {}

        params['tracking_blur'] = self.tp_tracking_blur
        params['repair_iterations'] = self.tp_repair_iterations
        params['thresh_lo'] = self.threshInitial[0]
        params['thresh_hi'] = self.threshInitial[1]
        params['threshes'] = copy.copy(self.threshes)

        return params

    
    def trackFrame(self, b_log=False):
        '''
            Wrapper function for a particular trackAlgo:
                - unpack parameters
                - select the particular track algo to run
                - [possibly] time the function (if self.bTrackTimer)
                - [possibly] return log of img transform steps (if b_log)

            questions/todos:
                [ ] pass in objEnum to trackAlgo for multi-obj tracking

        '''

        if not(self.on): return

        tracking_blur = self.tp_tracking_blur
        repair_iterations = self.tp_repair_iterations 

        thresh_lo = self.threshInitial[0]
        thresh_hi = self.threshInitial[1]

        threshes = copy.copy(self.threshes)

        if self.bTrackTimer:
            t0 = time.time()

        ret = None

        if self.tp_trackAlgoEnum == 0:
            
            ret = self.trackDefault(
                         tracking_blur = tracking_blur
                        ,repair_iterations = repair_iterations
                        ,thresh_lo = thresh_lo
                        ,thresh_hi = thresh_hi
                        ,b_log = b_log
                        ,objEnum = 0  #TODO-SS
            )

        elif self.tp_trackAlgoEnum == 1:
            
            ret = self.trackDemoNew(
                         tracking_blur = tracking_blur
                        ,repair_iterations = repair_iterations
                        ,thresh_lo = thresh_lo
                        ,thresh_hi = thresh_hi
                        ,b_log = b_log
                        # ,objEnum = 0
            )

        elif self.tp_trackAlgoEnum == 2:
            
            ret = self.trackMultiThresh1(
                         tracking_blur = tracking_blur
                        ,repair_iterations = repair_iterations
                        ,threshes = threshes
                        ,b_log = b_log
                        # ,objEnum = 0
            )
        else:
            print 'trackAlgoEnum not recognized'

        if self.bTrackTimer:
            if self.currentFrameInd not in self.trackTimerData.keys():
                t_proc = time.time() - t0
                self.trackTimerData[self.currentFrameInd] = t_proc

        if ret is not None:
            return ret

        
    # tracker algos --------

    def trackDefault(self
                    ,tracking_blur
                    ,repair_iterations
                    ,thresh_lo
                    ,thresh_hi
                    ,b_log = False
                    ,objEnum = 0
                    ):
        '''
            trackDefault:

                Template for writing a track algo.

                - add documentation notes, describing how this algo is different;
                  in this case we're describing the templating.

                 - organize all parameters used in func args; these are
                   retreived from the instance in parent function, trackFrame,
                   and thus read-only.
                    - add b_log and objEnum defaults to args

                 - write trackAlgo output data to instance properties:
                    self.currentTrackSuccess
                    self.currentTrackScore  (as a DataSchema.ScoreSchema)

                 - return None, unless b_log

                    - in which case, include a b_log section:
                        - add all possible transforms to 'keys' list.
                        - set 'data' for each possible key, mimicing control flow
                          for early return in the function
                        (this will be used to debug in notebooks, but is
                         not necessary for most purposes.)

            questions / todos:

                [ ] will we overwrite data before it hits b_log return data?

        '''

        img_t = transformA(self.currentFrame.copy(), tracking_blur)
        
        img_mask = threshA(  img_t 
                            ,threshLo = thresh_lo   
                            ,threshHi = thresh_hi ) 

        if not(img_mask is None) and (img_mask.sum() != 0):

            img_mask_2 = repairA(img_mask, iterations = repair_iterations)

            x,y = find_xy(img_mask_2)
            radius = find_radius(img_mask_2)
                    
            if radius > 0:
                self.currentTrackSuccess = True

                self.currentTrackScore.addCircle(
                                     self.circleToRect((x,y,radius))
                                    ,objEnum=objEnum
                                    )
            else:
                self.currentTrackSuccess = False
                self.currentTrackScore.reset()

        else:
            self.currentTrackSuccess = False
            self.currentTrackScore.reset()

        if b_log:
            
            keys = ['img_t','img_mask','img_repair','xy', 'radius', 'scoreCircle']
            data = OrderedDict()
            for k in keys:
                data[k] = None

            data['img_t'] = img_t
            data['img_mask'] = img_mask
            
            if img_mask is not None:
                data['img_repair'] = img_mask_2
                data['xy'] = (x,y)
                data['radius'] = radius
                data['scoreCircle'] = self.currentTrackScore.getObjRect(0)
            
            return data

    def trackDemoNew(self
                    ,tracking_blur
                    ,repair_iterations
                    ,thresh_lo
                    ,thresh_hi
                    ,b_log = False
                    ):
        '''
            trackDemoNew:

                Example for adding a non-default trackAlgo.

                Only a few small changes to this function:

                    - allow us to bypass repairA step by setting 
                      repair_iterations to 0

                    - early return when img_mask is blank
                
            questions / todos:

                [x] verify early return skips a section and verify the notebook
                    workflow process handles the missing data gracefully 
                    in mutliPlot()
                [ ] is a tracking_blur = 1 do any changes?
                [ ] does repair_iteration = 0 work in trackDefault()?

        '''

        img_t = transformA(self.currentFrame.copy(), tracking_blur)
        
        img_mask = threshA(  img_t 
                            ,threshLo = thresh_lo   
                            ,threshHi = thresh_hi ) 

        if img_mask.sum() != 0:

            if repair_iterations > 0:
                img_repair = repairA(img_mask, iterations = repair_iterations)
                img_terminal = img_repair
            else:
                img_terminal = img_mask

            x,y = find_xy(img_terminal)
            radius = find_radius(img_terminal)
                    
            if radius > 0:
                
                self.currentTrackSuccess = True

                self.currentTrackScore.addCircle(
                                            self.circleToRect((x,y,radius))
                                            ,objEnum=0   
                                        )
            else:
                self.currentTrackSuccess = False
                self.currentTrackScore.reset()

        else:
            self.currentTrackSuccess = False
            self.currentTrackScore.reset()

        if b_log:
            
            keys = ['img_t','img_mask','img_repair', 'img_terminal',
                    'xy', 'radius', 'scoreCircle']
            data = OrderedDict()
            for k in keys:
                data[k] = None

            data['img_t'] = img_t
            data['img_mask'] = img_mask
            
            if img_mask.sum() != 0:
                data['img_terminal'] = img_terminal
                data['xy'] = (x,y)
                data['radius'] = radius
                if repair_iterations > 0:
                    data['img_repair'] = img_repair
                if radius > 0:
                    data['scoreCircle'] = self.currentTrackScore.getObjRect(0)
            
            return data

    def trackMultiThresh1(self
                    ,tracking_blur
                    ,repair_iterations
                    ,threshes
                    ,b_log = False
                    ):
        '''
            trackMultiThresh1:

                Evolved from trackDemoNew; uses multiple thresh intervals
                
            questions / todos:

                [ ] multiple threshes

        '''

        img_t = transformA(self.currentFrame.copy(), tracking_blur)
        
        img_mask = threshMultiOr(  img_t 
                                  ,threshes = threshes
                                ) 

        if img_mask.sum() != 0:

            if repair_iterations > 0:
                img_repair = repairA(img_mask, iterations = repair_iterations)
                img_terminal = img_repair
            else:
                img_terminal = img_mask

            x,y = find_xy(img_terminal)
            radius = find_radius(img_terminal)
                    
            if radius > 0:
                
                self.currentTrackSuccess = True

                self.currentTrackScore.addCircle(
                                            self.circleToRect((x,y,radius))
                                            ,objEnum=0   
                                        )
            else:
                self.currentTrackSuccess = False
                self.currentTrackScore.reset()
        
        else:
            self.currentTrackSuccess = False
            self.currentTrackScore.reset()

        if b_log:
            
            keys = ['img_t','img_mask','img_repair', 'img_terminal',
                    'xy', 'radius', 'scoreCircle']
            data = OrderedDict()
            for k in keys:
                data[k] = None

            data['img_t'] = img_t
            data['img_mask'] = img_mask
            
            if img_mask.sum() != 0:
                data['img_terminal'] = img_terminal
                data['xy'] = (x,y)
                data['radius'] = radius
                if repair_iterations > 0:
                    data['img_repair'] = img_repair
                if radius > 0:
                    data['scoreCircle'] = self.currentTrackScore.getObjRect(0)
            
            return data


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
