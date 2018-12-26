import sys, copy, random, subprocess, time
import pickle
import cv2
import numpy as np
import io
from PIL import Image
from collections import OrderedDict
from itertools import combinations
from Interproc import DBInterface
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from Interproc import GuiviewState
from ControlTracking import TrackFactory
from ControlDisplay import Display



class EvalTracker:

    '''
        Different ways to evaluate if the ScoreSchema output from a trackFrame
        matches expectations.

        inputs are full scoring-dict, within this class we index the scoring-dict
        with 'objEnum' and 'data' keys

            e.g. EvalTracker.setBaselineScore(gs.displayInputScore)
                 (where gs.displayInputScore is a score-dict)

    '''
    
    def __init__(self):
        self.baselineScore = None
        self.objEnum = '0'

    def setObjEnum(self, sObjEnum):
        self.objEnum = str(sObjEnum)

    def setBaselineScore(self, baselineScore):
        self.baselineScore = copy.deepcopy(baselineScore)

    def distanceFromBaseline(self, inputScore):
        ''' cartesian distance from center of inputScore to baseline;
            for score-type=circle only
        '''
        
        if not(self.checkTrackSuccess(inputScore)):
            return 9999.9

        xA, yA, rA = Display.rectToCircle(inputScore[self.objEnum]['data'])
        xB, yB, rB = Display.rectToCircle(self.baselineScore[self.objEnum]['data'])

        cartDistance = ((xA - xB)**2 + (yA - yB)**2)**(0.5)

        return cartDistance

    def checkTrackSuccess(self, trackScore):
        ''' easiest way to check a ScoreSchema if track returned True '''
        try:
            if trackScore[self.objEnum]['data'] == (0,0,0,0):
                return False
            return True
        except:
            return False

    def checkTrackInsideBaselineRect(self, inputScore):
        '''
            check if the center on inputScore is inside the baslineScore
            important: this uses rect, not circle    
        '''
        
        if not(self.checkTrackSuccess(inputScore)):
            return False

        _x, _y, _dx, _dy = inputScore['0']['data']
        x, y, dx, dy = self.baselineScore['0']['data']

        if not((_x > x) and (_x < x + dx)):
            return False

        if not((_y > y) and (_y < y + dy)):        
            return False
        
        return True

    def checkTrackInsideBaseline(self, inputScore):
        '''
            check if the center on inputScore is inside the baslineScore
            considered as a circle
                
        '''
        
        if not(self.checkTrackSuccess(inputScore)):
            return False

        xB, yB, rB = Display.rectToCircle(self.baselineScore[self.objEnum]['data'])

        dist = self.distanceFromBaseline(inputScore)

        if dist < rB:
            return True

        return False


    def checkBaselineInsideTrack(self, inputScore):
        '''
            check if the center on baselineScore is inside the trackScore
                currently inside rect; todo - check for inside a circle
        '''
        
        if not(self.checkTrackSuccess(inputScore)):
            return False

        xA, yA, rA = Display.rectToCircle(inputScore[self.objEnum]['data'])

        dist = self.distanceFromBaseline(inputScore)

        if dist < rA:
            return True

        return False

    def checkEitherContainsOther(self, inputScore):
        ''' either track-center is inside baseline-score-circle or
            baseline-score-center is inside track-center-circle. '''

        return ( self.checkBaselineInsideTrack(inputScore) or
                self.checkTrackInsideBaseline(inputScore))

    def checkBothContainsOther(self, inputScore):
        ''' both track-center is inside baseline-score-circle and
            baseline-score-center is inside track-center-circle. '''

        return ( self.checkBaselineInsideTrack(inputScore) and
                self.checkTrackInsideBaseline(inputScore))


    def compareRadii(self, inputScore):
        '''
            compare size of the radius;
            positive: track is larger; nnegative: baseline is larger
        '''
        
        xA, yA, rA = Display.rectToCircle(inputScore[self.objEnum]['data'])
        xB, yB, rB = Display.rectToCircle(self.baselineScore[self.objEnum]['data'])

        if ((rA > 0.0) and (rB > 0.0)):
            return (rA - rB)
        else:
            return 0.0

        



    def checkTrackInWindow(self, inputScore, zoomRect):
        '''
            check if inputScore is inside the zoomWindow
            question: is zoomrect relative to Orig or to Main?
        '''
        pass