import sys, copy, random, subprocess, time
import pickle
import cv2
import numpy as np
import pandas as pd
import io
import sqlalchemy
import tempfile
from PIL import Image
from collections import OrderedDict
from itertools import combinations
from Interproc import DBInterface
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from Interproc import GuiviewState
from ControlTracking import TrackFactory
from ControlDisplay import Display
from ImgUtils import crop_img

'''
    functions to use in jupyter notebooks to debug different
    trackers under different scenarios

'''

def applyTracker(listGS, tracker, roiSelectFunc = None, 
                roiSelectParams = {}, bLogPlts = True):
    ''' 
        pass in:
         listGS -  list of GuiviewState objs; "states"
         tracker - one trackFactory obj; applied to all states
         roiSelectFunc - a function that takes a guiviewstate obj
                    as an argument, and returns an image
         bLogPlts - bool for outputting data['listPlts']

        returns dict:
         listScore - list of ScoreSchema obj's; one for each state
         listPlts - list of list of np.arrays (or None) representing
                    an image within the trackAlgo pipeline. 
                    outer list: one for each state
                    inner list: one for each transform in trackAlgo
         listTransformTitles - list of variable names corresponding to
                    img transforms within trackAlgo
         listFrameTitles - list of frame-indexes
            
    '''
    
    listData = []
    listScore = []
    listPlts = []
    listTransformTitles = []
    listFrameTitles = []

    for _gs in listGS:

        _gs.initDisplay()

        if roiSelectFunc is None:
            img = _gs.getOrigFrame()
        else:
            img = roiSelectFunc(_gs, **roiSelectParams)

        
        tracker.setFrame(img)

        listData.append( tracker.trackFrame(b_log=True) )

        listScore.append( tracker.getTrackScore())

        listFrameTitles.append( str(_gs.frameCounter) )

    if bLogPlts:

        for _data in listData:

            for _key in _data.keys():

                try:
                    assert _data[_key].shape[0] > 0
                    assert _data[_key].shape[1] > 0
                except:
                    continue     # not an image; bypass

                # build list of all keys in all tracking scenarios;
                # this way we'll include a record for that transform 
                # for each Frame for an NxM-aligned subplots
                
                if _key not in listTransformTitles:
                    listTransformTitles.append(_key)
            
        for _data in listData:
        
            listTmp = []
            
            for _transformTitle in listTransformTitles:
                
                # inclue the image-data from this transform;
                # if that transform doesn't exist, mark as None.
                
                try:
                    outputData = _data[_transformTitle]
                except:
                    outputData = None
                    
                listTmp.append( outputData )

            listPlts.append( listTmp )
    
    ret = {}
    ret['listPlts'] = listPlts
    ret['listScore'] = listScore
    ret['listFrameTitles'] = listFrameTitles
    ret['listTransformTitles'] = listTransformTitles
                            
    return ret



def getAnnotatedScoreFrame(gs, tracker, score_rect=None, expand_factor=None):
    '''
        return an annotated image from the gs-obj and tracker-obj; for use as
        'MarkedFrame' in compareTrackers(). Uses the same pattern as guiview
        for utilizing the Display class to draw/annotate onto an img/img-roi.
        
        input: gs-obj, tracker-obj
        return img (np.array of dims (h,w,num_color_channels))

        why/how we do it:

            step1
            perfrom a trackFrame() to get the track_score for annotation
            the data for input_score should already exist in gs-obj if it exists

            step1a
            if we enter a score_rect, we want to override the [possible] exisiting
            scoreRect within the gs-obj

            step2
            if we need to expand the marked_frame field of view use expand_factor
            build a new scoreFrame in the Display obj contained in gs

            step3
            apply annotations through Display-api, these operate on Display contained
            data objects like .scoreFrame
            note: we change line thickness b/c a resize occurs to bring these windows
            to roughly shape=(240,320)

            step4
            return the scoreFrame

    '''
    gs.initDisplay()
    
    # step1
    tracker.setFrame(gs.getOrigFrame())
    tracker.trackFrame()
    track_score = tracker.getTrackScore()

    # step1a
    if score_rect is None:
        scoreRect = gs.display.scoreRect
    else:
        scoreRect = score_rect
    
    # step2
    if expand_factor is not None:

        scoreRect = Display.zoomInRect( scoreRect
                                        ,zoomFct=expand_factor
                                        ,b_zoomout=True)
    
    gs.display.scoreRect = scoreRect    
    gs.display.scoreFrame = gs.display.buildScoreFrame()

    
    # step3
    gs.display.setTrack(trackScore = track_score)
    gs.display.drawOperators(score_thick = 4)
    gs.display.drawTrackers(score_thick = 4)
    
    return gs.display.scoreFrame.copy()


def compareTrackers(listGS, listTrackers, roiSelectFunc=False, bMarkedFrame=True
                    ,bTrackScore=False, bFirstTrackerRoi=False, **kwargs):
    '''
        plot side-by-side results of different trackers on frame(s)
        
        input:
            
            listGS          - (list of GS-objs), they don't have to be initialized.
            
            listTrackers    - (list of TrackFactory-objs), already initialized
                                and configured.
            
            roiSelectFunc   - (bool) if True, select the window-roi around the 
                                input_score or track_score. bTrackScore and 
                                expand_factor will further affect this window

            bMarkedFrame    - (bool) add a top image showing circles for input_score
                                and track_score

            bTrackScore     - (bool) use the track_score (instead of input_score when
                                available) to provide coords for window-roi

            bFirstTrackerRoi- (bool) if True, use the window-roi from the first tracker
                                 for all the other trackers in  the list.
                                 recommended to use in conjunction with bTrackScore=True
            
            kwargs          - formatting/configuration suggestions:
                
                expand_factor - (float) expand the frame (from default size) by 
                                that factor. used for viewing off-ball tracks
                test_stub      - (bool) if True will return a dict with data
                                 instead of plot display
                col_titles    - (list of str) overide default labels for columns 
                                to denote which algo method corresponds to that col
                                e.g. ['repairIters=0', 'repairIters=1']
                multiplot_params - (dict) {arg_name1: arg_val1, arg_name2: arg_val2, ...}
                                   for passing into mutliPlot() e.g. {'figsize':(20,20)}
                blend_rowtitles - (bool) don't align img frames by transform-name 
                                        between algos, simply list them in the order 
                                        they exist within their respective track_log
                
        output:
            None; will simply display to calling jupyter notebook


    '''
    
    # get optional args which alter control flow of output
    expand_factor = kwargs.get('expand_factor')
    
    roiSelectParams = {}
    if expand_factor is not None:
        roiSelectParams = {'expand_factor': expand_factor}

    b_blend_rowtitles = kwargs.get('blend_rowtitles', False)

    # helper functions
    def addOrAppend(d_data, key, val):
        ''' if key is present, append val to list of that key;
            otherwise, add the key and that val as a 1-elem list
        '''
        try:
            if key in d_data.keys():
                d_data[key].append(val)
            else:
                d_data[key] = [val]
        except:
            pass
        return d_data

    def addNonesForEmpties(d_data, s_keys):
        ''' add Nones where d_data.values (which are lists) but are empty 
            in current position 
        '''
        width = max(map(lambda elem: len(elem), d_data.values()))
        for _k in d_data.keys():
            if len(d_data[_k]) < width:
                if _k in s_keys:
                    # if this is a new key prepend Nones for all
                    # previous algos
                    prev_value = copy.deepcopy(d_data[_k])[0]
                    prepend = [None for _ in range(width - 1)]
                    prepend.append(prev_value)
                    d_data[_k] = prepend
                else:
                    # if this is an existing key without a value in this col
                    # simply add a None to the next position
                    d_data[_k].append(None)
        return d_data

    def updateOrderDict(order_dict, tmp_names):
        ''' if there's a new key/row_title, add it at its current position 
            and shift all higher values up one
        '''
        for _i, _name in enumerate(tmp_names):

            if _name in order_dict.keys():
                continue
            else:
                if _i == 0:
                    new_i = 0
                else:
                    new_i = order_dict[tmp_names[_i-1]] + 1
                for _item in order_dict.items():
                    k, v = _item[0], _item[1]
                    if v >= new_i:
                        order_dict[k] = v + 1
                order_dict[_name] = new_i
        return order_dict

    def getOrderSorted(order_dict):
        ''' return the keys/titles in ASC order based on '''
        items = order_dict.items()
        items.sort(key = lambda elem: elem[1])
        ret = [elem[0] for elem in items]
        return ret

    def transformListListRows(list_list_rows):
        ''' convert to list of strings with each row_title 
            carriage-separated for it's respective col
        '''        
        height = max(map(len, list_list_rows))
        width = len(list_list_rows)
        
        ret = []

        for _irow in range(height):
            
            tmp = []
            
            for _icol in range(width):

                try:
                    tmp.append(list_list_rows[_icol][_irow])
                except:
                    tmp.append("n/a")

            _rowtitle = '\n'.join(tmp)
            
            ret.append(_rowtitle)

        return ret


    # top-of-the-loop, loop over frames
    for _gs in listGS:

        # reset all data for each frame
        plot_dict = OrderedDict()
        plot_order_dict = {}
        col_titles, row_titles = [], []
        algo_enums = []
        row_titles_order = []
        cropped_rects = []
    
        for _itracker, _tracker in enumerate(listTrackers):
    
            # return a dict of information from the _tracker's tracker_log 
            data = applyTracker( [_gs]
                                ,_tracker
                                ,roiSelectFunc=None
                                )

            tmp_plts = copy.deepcopy(data['listPlts'][0])
            tmp_names = copy.copy(data['listTransformTitles'])
            tmp_score = data['listScore'][0]

            # set plot_crop_rect for future cropping of roi
            obj_enum = 0

            if not(bFirstTrackerRoi) or (_itracker==0):
            
                # which data source is used to build roi
                b_input_score = (_gs.displayInputScore is not None)
                
                if b_input_score:
                    plot_crop_rect = _gs.displayInputScore[str(obj_enum)]['data']
                
                if bTrackScore or not(b_input_score):
                    plot_crop_rect = tmp_score[str(obj_enum)]['data']

                # now expand the rect as needed
                initial_expand_factor = 0.1  # match Display.alterFrame behavior
                input_expand_factor = (expand_factor 
                                        if expand_factor is not None else 0.0)
                total_expand_factor = initial_expand_factor + input_expand_factor
                
                plot_crop_rect = Display.zoomInRect2(  copy.copy(plot_crop_rect)
                                                ,zoomFct=total_expand_factor
                                                ,b_zoomout=True)

            # an additional img which shows track/score drawn onto frame
            if bMarkedFrame:
                
                marked_frame = getAnnotatedScoreFrame(  
                                             _gs
                                            ,_tracker
                                            ,score_rect=copy.copy(plot_crop_rect)
                                            ,expand_factor=None
                                            )
                
                plot_dict = addOrAppend(plot_dict, 'marked_frame', marked_frame)
            
            
            #crop diagnostic-plots here; crop based on track_score or input_score
            cropped_plts = []
            for _i, _plt in enumerate(tmp_plts):

                if not(roiSelectFunc):
                    cropped_plts.append(_plt)

                else:
                    try:
                        
                        
                        
                        crop_plt = crop_img(_plt, Display.absRect(plot_crop_rect))
                        
                        cropped_plts.append(crop_plt)
                        
                        if _i == 0:    
                            cropped_rects.append(str(plot_crop_rect))
                    
                    except:
                        cropped_plts.append(_plt)
                        if _i == 0:
                            cropped_rects.append('no_crop')

            # add all tracker_log images into dict; applyTracker() has already
            # separted tracker_log into listPlts/listTransformTitles using
            # the 'does this data element have a .shape property?' criterion
            for _i, _name in enumerate(tmp_names):
                
                _plt = cropped_plts[_i]

                plot_dict = addOrAppend(plot_dict, _name, _plt)

            plot_dict = addNonesForEmpties(plot_dict, tmp_names)

            # remember the order of the plots
            new_tmp_names = []
            if bMarkedFrame:
                new_tmp_names.append('marked_frame')
            new_tmp_names.extend(tmp_names)
            
            if b_blend_rowtitles:
                row_titles_order.append(new_tmp_names)
        
            # for _i, _name in enumerate(new_tmp_names):
            plot_order_dict = updateOrderDict(  plot_order_dict,
                                                copy.copy(new_tmp_names)
                                            )

            # log the tracker enums for use as col_titles
            algo_enums.append(_tracker.tp_trackAlgoEnum)

        
        # transform loop data into input data for multiPlot()
        if b_blend_rowtitles:
            # ordered_rows = list(plot_dict.keys())
            ordered_rows = getOrderSorted(plot_order_dict)
        else:
            ordered_rows = getOrderSorted(plot_order_dict)
        
        fig_title = 'FrameCounter=' + str(_gs.frameCounter)

        if b_blend_rowtitles:
            row_titles = transformListListRows(row_titles_order)
        else:
            row_titles = ordered_rows 

        tmp_col_titles = kwargs.get('col_titles', None)
        if tmp_col_titles is not None:
            col_titles = tmp_col_titles
        else:
            col_titles = ['AlgoEnum=' + str(enum) for enum in algo_enums]

        if bTrackScore or bFirstTrackerRoi:
            col_titles = [a + '\n' + b for a,b in zip(col_titles, cropped_rects)]

        # transform plot_dict info into input data for multiPlot()
        plot_data = []
        for _icol, _vcol in enumerate(col_titles):
            _tmp = []
            
            if b_blend_rowtitles:
                for _srow in row_titles_order[_icol]:
                    _tmp.append( plot_dict[_srow][_icol] )
            else:
                for _srow in ordered_rows:
                    _tmp.append( plot_dict[_srow][_icol] )
            plot_data.append(_tmp)

        # return data for testing
        if kwargs.get('test_stub', False):
            ret = {
                     'plot_dict':  plot_dict
                    ,'plot_data':  plot_data
                    ,'col_titles': col_titles
                    ,'row_titles': row_titles
            }
            return ret
                                        
        # plot each frame separately
        multiPlot(   list_list_imgs=plot_data
                    ,input_frame_titles=col_titles
                    ,input_transform_titles=row_titles
                    ,input_figure_title=fig_title
                    ,**kwargs.get('multiplot_params', {})
                    )



def roiSelectZoomWindow(inputGuiviewState):
    ''' a roiSelectFunc for use with applyTracker(); pass a *reference*
        to this function into that function 
    '''
    inputGuiviewState.initDisplay()
    return inputGuiviewState.getZoomWindow()

def roiSelectScoreWindow(inputGuiviewState, b_resize=False, expand_factor=None):
    ''' a roiSelectFunc for use with applyTracker(); pass a *reference*
        to this function into that function 
    '''
    inputGuiviewState.initDisplay()
    
    if b_resize:
        return inputGuiviewState.display.scoreFrame.copy()
    else:
        
        score_rect = inputGuiviewState.display.scoreRect
        
        if expand_factor is not None:
            score_rect = Display.zoomInRect( score_rect
                                            ,zoomFct=expand_factor
                                            ,b_zoomout=True)
        
        try:
            img = inputGuiviewState.getZoomWindow(inputRect=score_rect)
            return img
        except:
            return None




def buildImgComparisonData(listGS, tracker):
    ''' show intermediate mask data '''
    
    img_data = []
    
    for _gs in listGS:
        
        _tmp = []
        
        # scoreframe with track/score annotations
        
        tracker.setFrame(_gs.getOrigFrame())
        track_log = tracker.trackFrame(b_log=True)
        track_score = tracker.getTrackScore()
        
        _gs.initDisplay(zoomFct=0.5)
        _gs.drawTracker(track_score['0']['data'])
        _gs.drawOperator(_gs.displayInputScore['0']['data'])
        
        img = _gs.getScoreWindow()
        
        _tmp.append(img)
        
        # scoreframe tracker modified mask(s)
        
        _gs.initDisplay(zoomFct=0.5)
        cropped_img = _gs.getScoreWindow(bScoreFrame=False)
        
        tracker.setFrame(cropped_img)
        track_log = tracker.trackFrame(b_log=True)
        
        logs_of_interest = ['img_mask', 'img_terminal']
        
        for _log_key in logs_of_interest:
            
            _tmp.append(track_log[_log_key])

        img_data.append(_tmp)
        
    return img_data


class PixelConfusionMatrix:

    ''' build a confusion matrix for individual pixesl using:
            within pixel threshold value (positive's) 
            known circle location (true's) 
            their negation (~ operator) are negative's and false's respectively
    '''
    
    def __init__(self, **kwargs):
        
        self.img = kwargs.get('img', None)
        self.thresh = kwargs.get('thresh', None)
        self.threshes = kwargs.get('threshes', None)
        self.circle = kwargs.get('circle', None)

        self.circleMask = None
        self.threshMask = None
        
        self.tpMask = None
        self.fpMask = None
        self.tnMask = None
        self.fnMask = None

        self.tpPix = None
        self.fpPix = None
        self.tnPix = None
        self.fnPix = None
        
        self.N = None

        self.t = None
        self.f = None
        self.p = None
        self.n = None

        self.tp = None
        self.fp = None
        self.tn = None
        self.fn = None

        # for near the circle
        self.psuedoCircleMask = None
        self.pseudoFp = None
        self.pseudoFn = None

    def setImg(self, img):
        self.img = img.copy()

    def setThresh(self, thresh):
        self.thresh = thresh

    def setThreshes(self, threshes):
        self.threshes = copy.copy(threshes)

    def setCircle(self, scoreRect):
        self.circle = scoreRect

    def buildMasks(self):
        
        self.circleMask = self.buildCircularMask(
                                 self.img.shape[1]
                                ,self.img.shape[0]
                                ,*self.circleCenter(self.circle)
                                )

        self.threshMask = self.buildThreshMask()

    def calc(self):

        assert ((self.img is not None) and
                (self.circle is not None) and
                ((self.thresh is not None) or (self.threshes is not None))
               )

        self.buildMasks()
        
        self.tpMask = np.bitwise_and(self.threshMask, self.circleMask)
        self.fpMask = np.bitwise_and(self.threshMask, ~self.circleMask)
        self.tnMask = np.bitwise_and(~self.threshMask, ~self.circleMask)
        self.fnMask = np.bitwise_and(~self.threshMask, self.circleMask)

        self.tpPix = self.img[self.tpMask]
        self.fpPix = self.img[self.fpMask]
        self.tnPix = self.img[self.tnMask]
        self.fnPix = self.img[self.fnMask]

        self.N = self.img.shape[0] * self.img.shape[1]

        self.t = sum(sum(self.circleMask))
        self.f = (self.circleMask.shape[0] * self.circleMask.shape[1]) - self.t

        self.p = sum(sum(self.threshMask))
        self.n = (self.threshMask.shape[0] * self.threshMask.shape[1]) - self.p

        self.tp = self.tpPix.shape[0]
        self.fp = self.fpPix.shape[0]
        self.tn = self.tnPix.shape[0]
        self.fn = self.fnPix.shape[0]


    def getData(self):
        ''' data: list of the 3-ples; pixel data in each category '''
        ret = {}

        ret['tp'] = self.tpPix.copy()
        ret['fp'] = self.fpPix.copy()
        ret['tn'] = self.tnPix.copy()
        ret['fn'] = self.fnPix.copy()

        return ret

    def getVals(self, bN = True):
        ''' val: int; of the number of pixels in each category '''
        ret = {}
        
        ret['tp'] = self.tp if bN else float(self.tp) / float(self.N)
        ret['fp'] = self.fp if bN else float(self.fp) / float(self.N)
        ret['tn'] = self.tn if bN else float(self.tn) / float(self.N)
        ret['fn'] = self.fn if bN else float(self.fn) / float(self.N)

        ret['N'] = self.N if bN else 1.0

        ret['t'] = self.t if bN else float(self.t) / float(self.N)
        ret['f'] = self.f if bN else float(self.f) / float(self.N)
        ret['p'] = self.p if bN else float(self.p) / float(self.N)
        ret['n'] = self.n if bN else float(self.n) / float(self.N)

        return ret

    def displayVals(self, bN = True, places = 6):
        ''' printout a human readable display with formatting '''
        
        vals = self.getVals(bN = bN)

        #build output matrix
        data = [
                 [vals['N'], vals['t'],  vals['f']]
                ,[vals['p'], vals['tp'], vals['fp']]
                ,[vals['n'], vals['tn'], vals['fn']]
               ]

        #rounding
        if not(bN):
            data = map(lambda x: 
                        map(lambda y: 
                            y if isinstance(y, str) else round(y, places)
                        ,x)
                    ,data)

        colsList = [" ", "True", "False"]
        rowsList = [" ", "Positive", "Negative"]

        #printout
        rowFormat ="{:>15}" * (len(colsList) + 1)
        print rowFormat.format("", *colsList)
        
        for header, row in zip(rowsList, data):
            print rowFormat.format(header, *row)


    def buildThreshMask(self):
        
        if self.threshes is None:

            return np.array(
                            cv2.inRange(self.img, self.thresh[0], self.thresh[1])
                            ,dtype='bool'
                            )
            
            #TODO - replace cv2.inRange with numpy function

        else:

            #multi-thresh
            fullMask = np.array(np.zeros(shape = self.img.shape[:2]), dtype='bool')

            for _thresh in self.threshes:
                
                _mask = np.array(cv2.inRange(self.img, _thresh[0], _thresh[1])
                                            ,dtype='bool')
                
                fullMask = np.bitwise_or(fullMask, _mask)
            
            return fullMask

    @staticmethod
    def circleCenter(rect):
        _x,_y,_dx,_dy = rect
        x = _x + int(_dx/2)
        y = _y + int(_dy/2)
        r = min(int(_dx/2),int(_dy/2))
        return x,y,r

    @staticmethod
    def buildCircularMask(w, h, x, y, r):
        Y, X = np.ogrid[:h, :w]
        distFromCenter = np.sqrt((X - x)**2 + (Y - y)**2)
        mask = distFromCenter <= r
        return mask


# Data Prep Helper Func's for colorCube -------------------

def buildConfusionData(gs, inputThreshes, N = 1000, bOutputScore = True):
    ''' input:  gs             [guiview-state object]
                inputThreshes  [list of (2ple of 3ples)]

                bOutputScore - depends on the guiview-state, if the score
                    is in displayInput / displayOutput

        returns: pixelconfusionmatrix obj
    '''

    _img = gs.getOrigFrame()
    _threshes = inputThreshes

    if bOutputScore:
        _circle = gs.displayOutputScore['0']['data']
    else:
        _circle = gs.displayInputScore['0']['data']

    pcm = PixelConfusionMatrix( img = _img
                               ,threshes = _threshes
                               ,circle = _circle
                              )

    pcm.calc()

    return pcm


def buildConfusionPlotData(pcm, N = 1000):
    ''' input:  pcm           [PixelConsusionMatrix object]
                N             [int] - max sample amount
        
        returns: plotData [dict] with 4 entries from confusion mat
                                  with 3 channel int lists
    '''

    cm = pcm.getData()

    metrics = ['tp', 'fp', 'fn', 'tn']
    plotData = {}

    for metric in metrics:
        _data = cm[metric]
        plotData[metric] = pointsToList(
                        random.sample(_data, min(len(_data), N))
                         )
    return plotData



def imgToColors(img, sampleN = None):
    '''
        return list (len=3) of lists (len=num-pixels) of ints
        corresponding to pixel values of B, G, R respectively.

            sampleN: randomly sample and return N triplets

        TODOs:
            [ ] add random.seed stub for testing
    '''
    b, g, r = [list(img[:, :, clr].flatten()) for clr in  range(3)]

    if sampleN is not None:

        N = len(b)
        
        n = int(min(sampleN, N))

        listSample = random.sample(xrange(N), n)
        
        b = [b[i]for i in listSample]
        g = [g[i]for i in listSample]
        r = [r[i]for i in listSample]

    return b, g, r


def channelsToColorStr(listB, listG, listR):
    ''' input: BGR returns: '#'+RGB-hex-string
        example: with channelsToColorStr(*imgToColors(img))
    '''
    def twoDigit(strHex):
        strHex = strHex[2:]
        if len(strHex) == 1:
            strHex = '0' + strHex
        return strHex

    return [
        "#" + twoDigit(hex(x[0])) + twoDigit(hex(x[1])) + twoDigit(hex(x[2]))
        for x in zip(listR, listG, listB)
    ]


def colorInRange(data, threshes):
    ''' input: data as np.array shape (N, 3)
        output: list of int's (1 or 0) of len N
    '''
    _img = np.array(data, ndmin=3)
    
    or_inRangeX = np.array(np.zeros(shape = data.shape).T, dtype='bool')
    
    for _thresh in threshes:
        
        inRangeX = cv2.inRange(_img, _thresh[0], _thresh[1])
        
        inRangeX = np.array(inRangeX, dtype='bool')
    
        or_inRangeX = np.bitwise_or(inRangeX, or_inRangeX)

    return [int(v) for v in or_inRangeX[0]]    


def cvtPlot(img):
    ''' show the image after converting from bgr to rgb '''
    try:
        _img = cv2.cvtColor(img.copy(), cv2.COLOR_BGR2RGB)
    except:
        _img = img.copy()
    plt.imshow(_img)


# subprocess BatchOutput / Eval ------------------------------

def argsFromCmd(strCmd):
        strCmd = strCmd.replace("\t", "")
        strCmd = strCmd.replace("\n", " ")
        args = strCmd.split(" ")
        args = filter(lambda s: s != "", args)
        return args

def listToCommas(list_input):
    return ",".join(map(str, list_input))


def pollAndRead(proc, outLog, timeout=30):

    out_counter = 0
    sleep_interval = 0.001

    for _ in range(int( float(timeout) / float(sleep_interval) ) ):

        if proc.poll() is None:

            outLog.seek(out_counter)
            
            ret = outLog.read()

            if ret != '':
                out_counter += len(str(ret))
                sys.stdout.write(str(ret))
            
            time.sleep(sleep_interval)
            
        else:
            return
    
    print 'subproc timed out after %s seconds' % str(timeout)


def subprocBatchOutput(  f_pathfn
                        ,batch_enum = None
                        ,batch_list = None
                        ,db_pathfn = "data/usr/batch_tmp.db"
                        ,b_log = True
                        ):
    '''
        get a batch of guiview-state outputs based on defined criteria.

        return: listGS - list of GS objects

        input:  f_pathfn    - (str) pathfn to video file
                batch_enum  - (int) enum for batch-criteria
                batch_list  - (list of ints) frame-counters to output
                db_pathfn   - (str) path and fn for db for interproc-comm
                                    path is relative ppd/ root not calling 
                                    function
                b_log       - (bool) output the messages from stdout
    '''

    # validate
    if (int(batch_enum is not None) + int(batch_list is not None)) != 1:
        print 'must call with only one batch_xxx arg'
        return None

    # build args
    if batch_enum is not None:
        criteria_key = "--batchoutputenum"
        criteria_val = str(batch_enum)

    if batch_list is not None:
        criteria_key = "--batchoutputlist"
        criteria_val = listToCommas(batch_list)

    # build cmd
    cmd = '''python guiview.py --file %s %s %s %s %s''' % (
                                         f_pathfn
                                        ,criteria_key
                                        ,criteria_val
                                        ,'--batchdbpathfn'
                                        ,db_pathfn
                                        )
    args = argsFromCmd(cmd)

    #progressbar
    outLog = tempfile.SpooledTemporaryFile() if b_log else subprocess.PIPE
    
    # call subproc
    proc =  subprocess.Popen(    args
                                ,stderr = subprocess.PIPE
                                ,stdout = outLog
                                ,cwd = "../"
                                )
    # for progressbar
    if b_log:
        pollAndRead(proc, outLog)
    else:
        ret = proc.wait()

    # load from db - assume we're calling from ppd/books/
    db = DBInterface("../" + db_pathfn)     
    listGS = [pickle.loads(record[1]) for record in db.selectAll()]

    return listGS


def subprocEval( f_pathfn
                ,algo_enum = 0
                ,db_pathfn = "data/usr/eval_tmp.db"
                ,b_log = False
                ,b_eval_log = False
                ):
    '''
        get a outcome-dataframe by running guiview on a whole video.
        data path is relative to parent directory of calling kernel.

        return: df          - pandas dataframe

        input:  f_pathfn    - (str) pathfn to video file 
                                    (!relative to parent dir of calling kernel!)
                algo_enum   - (int) sent to ControlTracker via guiview cli
                db_pathfn   - (str) path and fn for db for interproc-comm
                                    path is relative ppd/ root not calling 
                                    function
                b_log       - (bool) write to stdout in jupyter notebook a 
                                    progress bar + process details
                b_eval_log  - (bool) output an high-level summaries of the results
    '''

    # build cmd
    cmd = '''python guiview.py --file %s 
                                --eval
                                --algoenum %s
                                --evaldbpathfn %s ''' % (
                                                f_pathfn
                                                ,str(algo_enum)
                                                ,db_pathfn
                                                )
    if b_eval_log:
        cmd += ' --evallog'

    args = argsFromCmd(cmd)
    
    outLog = tempfile.SpooledTemporaryFile() if b_log else subprocess.PIPE

    t0 = time.time()

    # call subproc
    proc =  subprocess.Popen(    args
                                ,stderr = subprocess.PIPE
                                ,stdout = outLog
                                ,cwd = "../"
                                )
    
    # for progressbar
    if b_log:
        pollAndRead(proc, outLog)
    else:
        ret = proc.wait()

    # load from db - assume we're calling from ppd/books/
    db_engine = sqlalchemy.create_engine('sqlite:///' + '../' + db_pathfn, echo=False)

    df = pd.read_sql_table('outcome_dataframe', con=db_engine)

    if b_log:
        total_time = str(time.time() - t0)
        print 'subproc time: %s' % total_time[:min(5, len(total_time))]

    return df


def loadOutcomeDataDf(db_pathfn="data/usr/eval_tmp.db"
                      ,tbl_name='outcome_dataframe'):
    ''' load from db and return pandas-df; assume we're calling from books/ dir '''
    
    db_engine = sqlalchemy.create_engine('sqlite:///' + '../' + db_pathfn, echo=False)

    return pd.read_sql_table(tbl_name, con=db_engine)


    


# colorCube -------------------------------------------------

def colorCube(  listB = None
               ,listG = None
               ,listR = None
               ,confData = {}
               ,regionMarkers = None
               ,listColors = None
               ,spaceTotal = True
               ,spaceDefined = {}
               ,viewPositionDefined = {}
               ,bInitPosition = False
               ,figsize = (10,10)
               ,bLegend = False
               ,bLegend2 = False
               ,title = None
               ,b_single = True
               ,b_save = False
               ,keyPressFunc = None
               ,axData = None
              ):
    '''
        3d plot of pixels color values

        (some arg's are for interactive-manipulation + interproc-comm)

        listB, listG, listR - [list] if not None, a single scatter plot with color
                              corresponding to listColors

        confData - [dict] where each key representing one element of confusion
                    matrix has a value of a list of bgr lists.
        
        regionMarkers - [list] representing thresh volume, if not none, 
                        a list of bgr lists

        listColors = [list] of '#00ff00'-style color strings
                     of len equal to listB
        
        spaceTotal - [bool] if True, whole support of each axis
                    is displayed: 0 to 255
        
        spaceDefined - [dict] with keys 'x', 'y', 'z' and a tuple 
                     corresponding to (lo, hi) values on that axis
        
        viewPositionDefined - [dict] with keys elevation and azimuth
                        that dictate an initial view position
        
        bInitPosition - [bool] set view-poisition when plt'd

        fisize - [tuple] of ints for size of figure

        bLegend - [bool] display a legend
        
        keyPressEvent - if not None, a reference to a function that
                        accepts a keyEvent arg and 
        
        axData -        if not None, a reference to a class instance method 
                        that attaches a reference to ax instance of a fig 
            
    '''
        
    plt.close()     #reset from previous interactive

    fig = plt.figure(figsize=figsize)

    ax = fig.add_subplot(111, projection='3d')


    #set view position
    if ((len(viewPositionDefined.keys()) > 0) and
        bInitPosition):
    
        ax.view_init(azim = viewPositionDefined.get('azimuth')
                    ,elev = viewPositionDefined.get('elevation')
        )
        
    #single scatter
    if ((listB is not None) and (listG is not None) and (listR is not None)):
        
        ax.scatter(xs=listB, ys=listG, zs=listR, c=listColors, marker='o')

    
    #multi-scatter: confusion matrix
    if len(confData.keys()) > 0:

        clrKey = OrderedDict({'tp': 'green', 'fp': 'yellow', 'fn': 'red', 'tn':'blue'})

        for _k in clrKey.keys():
        
            ax.scatter( *confData[_k] 
                        ,marker = 'o'
                        ,c = clrKey.get(_k, 'red') 
                        )
        

    #thresh volume plotting
    if regionMarkers is not None:
        ax.scatter(xs=regionMarkers[0], ys=regionMarkers[1], zs=regionMarkers[2], 
                    c='black', marker='^')

    #keypress utils
    if axData is not None:
        axData(ax)

    if keyPressFunc is not None:
        fig.canvas.mpl_connect('key_press_event', keyPressFunc)

    #set viewable space
    if spaceTotal and len(spaceDefined.keys()) == 0:
        ax.set_xlim3d(0, 255)
        ax.set_ylim3d(0, 255)
        ax.set_zlim3d(0, 255)
        
    if len(spaceDefined.keys()) > 0:
        if spaceDefined.get('x', None) is not None:
            ax.set_xlim3d(*spaceDefined['x'])
        if spaceDefined.get('y', None) is not None:
            ax.set_ylim3d(*spaceDefined['y'])
        if spaceDefined.get('z', None) is not None:
            ax.set_zlim3d(*spaceDefined['z'])
        
    #formatting
    if bLegend:
        legendArgs = []
        if (confData.keys() > 0):
            legendArgs += [str.upper(k) for k in clrKey.keys()]
        if (regionMarkers is not None):
            legendArgs += ['thresh-volume']
        plt.legend(legendArgs)

    if bLegend2:
        plt.legend()

    ax.set_xlabel('B')
    ax.set_ylabel('G')
    ax.set_zlabel('R')

    if title is not None:
        ax.set_title(title)

    if b_save:

        # output a saved png image
        
        # f = fig.gcf()
        # DefaultSize = f.get_size_inches()
        # print DefaultSize
        # fig.set_fig_size()
        # f.set_figsize_inches( (DefaultSize[0]*2, DefaultSize[1]*2) )
        
        # plt.axis('off')
        # plt.axes.get_xaxis().set_visible(False)
        # plt.axes.get_yaxis().set_visible(False)

        # fig.savefig(buf, format = 'png', bbox_inces='tight', pad_inches=0)
        
        buf = io.BytesIO()
        # fig.savefig(buf, format = 'png', dpi = 200)
        fig.savefig(buf, format = 'png', dpi = 'figure')
        buf.seek(0)
        ret = buf.read()
        buf.close()
        
        plt.close(fig)

        return ret

    else:

        plt.show()


    

class SubprocColorCube:

    ''' Class to save/load params for calling colorCube() in a subprocess;
        since it's a subproc, we need to transport the data with Interproc comm
        using pickle dump/load.
        Allows good "responsive" interactivity when called from jupyter but using a 
        true TK window outside browser.

        To Use:
        in jupyter: use helper function subprocColorCube() to build a class and output it
        then in terminal: cd to modules/; python AnalysisHelpers.py --subprocColorPlot;
                          this should produce the plot in separate window.
            use --dbpathfn [path/to/data.db] for specific book analysis

        Watchout:
            this class interfaces with pickle with self.loadedClass which itself is a 
            SubprocColorCube instance, and each dump/load seession goes off that, as
            does loadedClass.plot()

    '''

    def __init__(self
                ,listB = None
                ,listG = None
                ,listR = None
                ,listColors = None
                ,confData = {}
                ,spaceTotal = True
                ,spaceDefined = {}
                ,regionMarkers = None
                ,bInitPosition = True
                ,dbPathFn = None
                ):
        ''' set parameters to call colorCube() now, or later with set-methods below'''

        # colorCube params
        self.listB = listB
        self.listG = listG
        self.listR = listR
        self.listColors = listColors
        self.confData = confData
        self.spaceTotal = spaceTotal
        self.spaceDefined = spaceDefined
        self.regionMarkers = regionMarkers

        # plot params:
        self.bInitPosition = bInitPosition
        self.azimuth = None
        self.elevation = None
        self.distance = None
        self.ax = None

        # interprocess comm helpers
        if dbPathFn is None:
            self.dbPathFn = "../data/usr/interproc_colorcube.db"
        else:
            self.dbPathFn = dbPathFn
        self.db = None
        self.loadedClass = None

    #helper set-methods: for loading data piece-wise -----
    
    def setListX(self, listB, listG, listR):
        self.listB = copy.copy(listB)
        self.listG = copy.copy(listG)
        self.listR = copy.copy(listR)

    def setListColors(self, listColors):
        self.listColors = copy.copy(listColors)

    def setParams(self, spaceTotal = None, spaceDefined = None):
        if spaceTotal is not None:
            self.spaceTotal = spaceTotal
        if spaceDefined is not None:
            self.spaceDefined = copy.copy(spaceDefined)


    # interproc methods ------

    def save(self):
        _db = DBInterface(self.dbPathFn)
        _db.insertState(pickle.dumps(self))

    def load(self):
        ''' load the most recent entry from colorplot_tbl into 
            self.loadedClass '''
        
        try:
            _db = DBInterface(self.dbPathFn)
            recentRecord = _db.selectLatest()
        except:
            print 'could not load colorplot_tbl record'

        try:
            self.loadedClass = pickle.loads(recentRecord[0][1])
            print 'loaded class type: ', str(self.loadedClass.__class__.__name__)
        except Exception as e:
            print 'could not load SubprocColorCube class with pickle'
            print e

    
    # plotting methods; invoked on self.loadedClass -------
    
    def callPlot(self, bInitPosition=True, bInteractive=False):
        ''' main method for running a subprocess colorCube() '''
        self.loadedClass.plot(bInitPosition=bInitPosition, bInteractive=bInteractive)
    
    
    def plot(self, bInitPosition=True, bInteractive=False):
        ''' invoke the colorCube function '''
        
        viewPositionDefined = {}
        keyPressSubproc = None
        setAxData = None

        if bInitPosition:
            viewPositionDefined['azimuth'] = self.azimuth
            viewPositionDefined['elevation'] = self.elevation
            
        if bInteractive:
            keyPressSubproc =  self.keyPressSubproc
            setAxData = self.setAxData
        
        colorCube(
                  listB = self.listB
                 ,listG = self.listG
                 ,listR = self.listR
                 ,listColors = self.listColors
                 ,confData = self.confData
                 ,spaceTotal = self.spaceTotal
                 ,spaceDefined = self.spaceDefined
                 ,viewPositionDefined  = viewPositionDefined
                 ,bInitPosition = bInitPosition
                 ,regionMarkers = self.regionMarkers
                 ,keyPressFunc=keyPressSubproc
                 ,axData = setAxData
                 )

    # helper-pass-ins for interactive state ------
    
    def setAxData(self, axObj):
        ''' stores a reference to ax object created from the fig in an interactive-
            enabled colorCube; used in keyPressSubproc to get viewing-position data
        '''
        self.ax = axObj

    def resetAxData(self):
        ''' call this before save() to avoid pickling ax obj '''
        self.ax = None
    
    def keyPressSubproc(self, event):  
        ''' pass this in to colorCube to handle keypress events here'''
        
        if event.key == 'o':
            self.azimuth = self.ax.azim
            self.elevation = self.ax.elev
            print 'outputting  view pos params to interproc %s , %s' % (
                                        str(self.azimuth)[:5], str(self.elevation)[:5]
                                        )
            
            self.resetAxData()
            self.save()     # this will save self.loadedClass to db
        else:
            print '%s :command not recognized.' % event.key



def subprocColorCube(
                 listB = None
                ,listG = None
                ,listR = None
                ,listColors = None
                ,confData = {}
                ,spaceTotal = True
                ,spaceDefined = {}
                ,regionMarkers = None
                ,dbPathFn = None
                ):
    
    ''' helper function for outputting an instance SubprocColorCube from
        jupyter into an interproc db '''
    
    subprocClass = SubprocColorCube(
                 listB = listB
                ,listG = listG
                ,listR = listR
                ,listColors = listColors
                ,confData = confData
                ,spaceTotal = spaceTotal
                ,spaceDefined = spaceDefined
                ,regionMarkers = regionMarkers
                ,dbPathFn = dbPathFn
                )
    
    subprocClass.save()

    #PROBLEM: matplotlib doesn't output when called from jupyter
        # running subprocess calling colorCube
        # <Figure size 640x480 with 1 Axes>

# colorcube helpers like regionMarkers --------------

def threshToCorners(threshLo, threshHi):
    ''' output 8 3-ples from input 2 3-ples'''
    
    ret = []
    threshes = [list(threshLo)]
    threshes.append(list(threshHi))
    
    for _x in range(2):
        for _y in range(2):
            for _z in range(2):
                
                    x = threshes[_x][0]
                    y = threshes[_y][1]
                    z = threshes[_z][2]
                    
                    ret.append((x,y,z))
                    
    return ret

def pointsToList(points):
    ''' slices list of points into respective x,y,z value lists for input to plot()
        input: list of 3-ples, corresponding to points in color-space
        output: list (of length-3) of lists (of length=input-list-length),
                corresponding to 
        [(10,10,20), (20,20,0)] -> [[10,20],[10,20], [20,0]]
    '''
    return [[point[clr] for point in points] for clr in range(3)]

def cornersToCornerSets(corners):
    ''' input: list 
    
    '''
    cornerSets = (
        filter(lambda cornerSet: 2 == sum( [ 
                                    int((cornerSet[0][elem] - cornerSet[1][elem]) == 0)
                                    for elem in range(3)
                                    ])
            , [x for x in combinations(corners, 2)]
        )
    )
    return cornerSets

def cornerSetsToEdges(cornerSets, stepAmt = 5):
    ''' build a marker for each point along region edge at stepAmt intervals 
        input: list of 2-ples of 3-ples (corresponding 3D points)
        ouput: list of 3-ples (corresponding to all points on the edges)
    '''

    regionEdges = []

    for cornerSet in cornerSets:
        
        ind_step = [0 == (cornerSet[0][clr] - cornerSet[1][clr]) for clr in range(3)].index(False)
        
        step_lo = min(cornerSet[0][ind_step], cornerSet[1][ind_step])
        step_hi = max(cornerSet[0][ind_step], cornerSet[1][ind_step])
        
        inds_hold = [clr for clr in range(3) if clr != ind_step]
        
        for _step in range(step_lo, step_hi, stepAmt):
            
            _point = [0,0,0]
            
            for _hold in inds_hold:
                _point[_hold] = cornerSet[0][_hold]
                
            _point[ind_step] = _step
            
            regionEdges.append(_point)            

    return regionEdges

def threshToEdges(threshLo, threshHi, stepAmt = 5):
    ''' return edges of region from a threshold value; still need to convert
        3-ples with pointsToList() 
    '''
    return  cornerSetsToEdges(
                cornersToCornerSets(
                    threshToCorners(threshLo, threshHi)
                )
                ,stepAmt = stepAmt
            )

def buildRegionMarkers(threshes, stepAmt = 10):
    ''' return the volume edges for [multiple] thresh volumes
        as a 3-channel list of int's. '''

    regionMarkers = [[],[],[]]

    for _thresh in threshes:
    
        volume_i = pointsToList(
                        threshToEdges(
                                _thresh[0]
                                ,_thresh[1]
                                ,stepAmt = stepAmt
                        )
        )

        if len(volume_i[0]) > 0:
            
            for clr in range(len(regionMarkers)):
                regionMarkers[clr].extend(volume_i[clr])
    
    return regionMarkers


# multi-plotting helper functions -------

def confusionPlotByImage( listGS
                         ,inputThresh
                         ,N = 1000
                         ,viewPositionDefined = {}
                         ,regionStepAmt = 10
                         ,figsize = (10,10)
                         ,bOutputScore = True
                        ):
    ''' across each guiview-state, plot a color cube
    
        thresh held constant

        input a list og GS's, and a constant threshold

        TODO - make inputThresh multi-thresh
    '''
    
    for _gs in listGS:
        
        _pcm = buildConfusionData( _gs, [inputThresh]
                                        ,bOutputScore = bOutputScore)

        _plotData = buildConfusionPlotData(_pcm)
        
        _regionMarkers = buildRegionMarkers([inputThresh])
        
        _title = 'frame ' + str(_gs.frameCounter)
        
        colorCube( confData = _plotData
                  ,regionMarkers = _regionMarkers
                  ,title = _title
                  ,viewPositionDefined = viewPositionDefined
                  ,bInitPosition = True
                  ,figsize = figsize
                 )

def presetCubeViews():
    views = [
         ('green+blue' , {'azimuth': -81, 'elevation': 95})
        ,('green+red'  , {'azimuth': -166,'elevation': -4})
        ,('red+blue'   , {'azimuth': 81,  'elevation': 145})
    ]
        # other views to use
        # ('red+green' , {'elevation':12, 'azimuth': -178})
        # ('blue_green',  {'azimuth':89,'elevation': -115})
    return views

def confusionPlotByViews(    
                    confusionData
                    ,threshes
                    ,title=""
                    ,regionStepAmt = 10
                    ,figsize = (10,10)
                    ):
    ''' plot 3 different views of the same color cube '''
    
    views = presetCubeViews()
    
    _regionEdges = buildRegionMarkers(threshes, stepAmt = regionStepAmt) 
    
    for _view in views:
    
        _title = _view[0] + str(title)
    
        colorCube( confData = confusionData 
                  ,viewPositionDefined = _view[1]
                  ,title = _title
                  ,regionMarkers = _regionEdges
                  ,bInitPosition = True
                  ,figsize = figsize
                 )

# helpers to extract a png to a numpy array for display in multiPlot -------

def bytesToPic(bPic):
    arr = np.asarray(bytearray(bPic), dtype=np.uint8)
    pic = cv2.imdecode(arr, 1)
    return pic

def croppedPic(pic):
    deltaCrop = int( (float(1.9)/float(15.0)) * pic.shape[0]   )
    h,w = pic.shape[:2]
    pic_copy = pic.copy()
    crop = pic_copy[deltaCrop:h - deltaCrop,deltaCrop:w - deltaCrop ,:]
    return crop

def bytesToPic2(bPic):
    tmp = bytesToPic(bPic)
    return croppedPic(tmp)


def multiPlot(list_list_imgs
              ,b_cvt_color = True
              ,input_transform_titles = None
              ,input_frame_titles = None
              ,input_figure_title = None
              ,figsize = (10,10)  
              ,hspace = 0.3
              ,wspace = 0.3
              ,bGrid = True          
              ,bForceTitles = False
              ,bSupressDisplay = False
             ):
    '''
        output an N x M array of images
            N: number of states (width-wise)
            M: number of img-transforms (height-wise, descending order)

        input: 
            list_list_imgs: an outer-list of N states each with
                            an inner-list of M transforms.  
                            use applyTracker()['listPlts'] for this.
            input_xxx: list of strings; labelling titles
            b_cvt_color: account for cv2 vs pyplot array style

        TODO
            [ ] this doesn't work well for single images; fix that
    '''
    
    w = len(list_list_imgs)
    h = max(map(len, list_list_imgs))
    
    b_multiline = False
    if (h > 1) and (w > 1):
        b_multiline = True
    
    fig, ax = plt.subplots(h,w, figsize=figsize)
    
    fig.subplots_adjust(hspace=hspace)
    fig.subplots_adjust(wspace=wspace)
    
    if input_figure_title is not None:
        fig.suptitle(input_figure_title)
    
    for h_i in range(h):
        for w_i in range(w):
            
            
            # b_dummy: True if this data object is not an image
            # allows us to bypass exception-causing-operations ------
            b_dummy=False
            
            try:
                _img = list_list_imgs[w_i][h_i]
            except:
                b_dummy=True

            if _img is None:
                b_dummy = True

            dummy_img = np.array(np.zeros(shape=(10,10,3)), dtype='uint8')

            plt.box(False)
                
            # get axis and use it to display image / dummy-image -------
            if b_multiline:
                _ax = ax[h_i][w_i]
            else:
                _ax = ax[(h_i * w_i) + w_i]
                
            if not(b_dummy):
                _img = GuiviewState.cvtColor(_img.copy())
            
            try:
                if b_dummy:
                    _ax.imshow(dummy_img.copy())
                else:
                    _ax.imshow(_img)
            except:
                _ax.imshow(dummy_img.copy())
            
            # axis formatting -------------------------------------------
            if input_transform_titles is not None:
                if ((not(b_multiline) or w_i == 0) or bForceTitles):
                    _ax.set_ylabel(input_transform_titles[h_i])
                    
            if input_frame_titles is not None:
                if ((not(b_multiline) or h_i == 0) or bForceTitles):
                    _ax.set_title(input_frame_titles[w_i])

            if not(bGrid):
                _ax.tick_params(axis='x', colors=(0,0,0,0))
                _ax.tick_params(axis='y', colors=(0,0,0,0))
                _ax.axis('off')

    if not(bSupressDisplay):
        plt.show()



def exploreImgs(listGS, figw = 20):
    ''' for introductory dataset exploration; '''

    chart_data = []

    for _gs in listGS:
        _gs.initDisplay()
        tmp = []
        tmp.append(_gs.getOrigFrame())
        try:
            tmp.append(_gs.display.zoomFrame.copy())
        except:
            pass

        try:
            tmp.append(_gs.display.scoreFrame.copy())
        except:
            pass
        chart_data.append(tmp)

    titles = [_gs.frameCounter for _gs in listGS]

    multiPlot( chart_data, hspace = 0, wspace = 0, figsize = (figw, 2)
              ,input_frame_titles =   titles
              ,bForceTitles = False
              ,bGrid=False)


if __name__ == "__main__":


    # check for call to subprocColorCube
    if len(sys.argv) > 1:
        if sys.argv[1] == "--subprocColorCube":
            
            dbPathFn = None
            if len(sys.argv) > 2:
                if sys.argv[2] == '--dbpathfn':
                    dbPathFn = str(sys.argv[3])

            print 'running subprocess calling colorCube'

            p = SubprocColorCube(dbPathFn = dbPathFn)
            p.bInitPosition = False
            p.load()
            p.callPlot(bInitPosition=True, bInteractive=True)
            print 'done and exiting'
            


