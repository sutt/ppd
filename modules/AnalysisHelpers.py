import sys, copy, random, subprocess, time
import pickle
import cv2
import numpy as np
from collections import OrderedDict
from itertools import combinations
from Interproc import DBInterface
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from Interproc import GuiviewState
from ControlTracking import TrackFactory
from ControlDisplay import Display

'''
    functions to use in jupyter notebooks to debug different
    trackers under different scenarios

    TODOs
        [ ] inWindowCheck() returns True if trackScuess and center is
            in window
        [ ] add unit tests
        [ ] subprocColorPlot runs from jupyter instead of cmd-line
'''

def applyTracker(listGS, tracker, roiSelectFunc = None, bLogPlts = True):
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
            img = roiSelectFunc(_gs)

        
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


def roiSelectZoomWindow(inputGuiviewState):
    ''' a roiSelectFunc for use with applyTracker(); pass a *reference*
        to this function into that function 
    '''
    inputGuiviewState.initDisplay()
    return inputGuiviewState.getZoomWindow()



class EvalTracker:

    '''
        Different ways to evaluate if the ScoreSchema output from a trackFrame
        matches expectations.

    '''
    
    def __init__(self):
        self.baselineScore = None

    def setBaselineScore(self, baselineScore):
        self.baselineScore = copy.deepcopy(baselineScore)

    def distanceFromBaseline(self, inputScore):
        ''' cartesian distance from center of inputScore to baseline;
            for score-type=circle only
        '''
        
        if not(self.checkTrackSuccess(inputScore)):
            return 9999.9

        xA, yA, rA = Display.rectToCircle(inputScore['0']['data'])
        xB, yB, rB = Display.rectToCircle(self.baselineScore['0']['data'])

        cartDistance = ((xA - xB)**2 + (yA - yB)**2)**(0.5)

        return cartDistance

    @staticmethod
    def checkTrackSuccess(trackScore):
        ''' easiest way to check a ScoreSchema if track returned True '''
        try:
            if trackScore['0']['data'] == (0,0,0,0):
                return False
            return True
        except:
            return False

    def checkTrackInsideBaseline(self, inputScore):
        '''
            check if the center on inputScore is inside the baslineScore
                currently inside rect; todo - check for inside a circle
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

    #TODO - checkBaselineInsideTrack
    #TODO - checkEitherContainsOther() union trackInside, baselineInside

    def checkTrackInWindow(self, inputScore, zoomRect):
        '''
            check if inputScore is inside the zoomWindow
            question: is zoomrect relative to Orig or to Main?
        '''
        pass

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

        ret['N'] = self.n if bN else 1.0

        ret['t'] = self.t if bN else float(self.t) / float(self.N)
        ret['f'] = self.f if bN else float(self.f) / float(self.N)
        ret['p'] = self.p if bN else float(self.p) / float(self.N)
        ret['n'] = self.n if bN else float(self.n) / float(self.N)

        return ret

    def displayVals(self, bN = True, places = 6):
        ''' printout a human readable display with formatting '''
        vals = self.getVals(bN = bN)

        #some formatting thing....        


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

def cvtPlot(img):
    ''' show the image after converting from bgr to rgb '''
    _img = cv2.cvtColor(img.copy(), cv2.COLOR_BGR2RGB)
    plt.imshow(_img)


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
               ,title = None
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
            ax.set_xlim3d(spaceDefined['x'])
        if spaceDefined.get('y', None) is not None:
            ax.set_ylim3d(spaceDefined['y'])
        if spaceDefined.get('z', None) is not None:
            ax.set_zlim3d(spaceDefined['z'])
        
    #formatting
    if bLegend:
        legendArgs = []
        if (confData.keys() > 0):
            legendArgs += [str.upper(k) for k in clrKey.keys()]
        if (regionMarkers is not None):
            legendArgs += ['thresh-volume']
        plt.legend(legendArgs)

    ax.set_xlabel('B')
    ax.set_ylabel('G')
    ax.set_zlabel('R')

    if title is not None:
        ax.set_title(title)

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

     



def multiPlot(list_list_imgs
              ,b_cvt_color = True
              ,input_transform_titles = None
              ,input_frame_titles = None
              ,input_figure_title = None
              ,figsize = (10,10)            
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
    '''
    
    w = len(list_list_imgs)
    h = len(list_list_imgs[0])     
    
    b_multiline = False
    if (h > 1) and (w > 1):
        b_multiline = True
    
    fig, ax = plt.subplots(h,w, figsize=figsize)
    
    fig.subplots_adjust(hspace=0.3)
    
    if input_figure_title is not None:
        fig.suptitle(input_figure_title)
    
    for h_i in range(h):
        for w_i in range(w):
            
            if list_list_imgs[w_i][h_i] is None:
                continue
                
            _img = list_list_imgs[w_i][h_i]
            _img = GuiviewState.cvtColor(_img.copy())
            
            if b_multiline:
                _ax = ax[h_i][w_i]
            else:
                _ax = ax[(h_i * w_i) + w_i]
                
            _ax.imshow(_img)
            
            if input_transform_titles is not None:
                if (not(b_multiline) or w_i == 0) :
                    _ax.set_ylabel(input_transform_titles[h_i])
                    
            if input_frame_titles is not None:
                if (not(b_multiline) or h_i == 0) :
                    _ax.set_title(input_frame_titles[w_i])
    
    plt.show()


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
            


