import sys, copy, random, subprocess, time
import pickle
import cv2
import numpy as np
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

def colorCube(listB, listG, listR
               ,dictData = {}
               ,listColors = None
               ,spaceTotal = True
               ,spaceDefined = {}
               ,viewPoisitonDefined = {}
               ,regionMarkers = None
               ,bInitPosition = False
               ,keyPressFunc = None
               ,axData = None
              ):
    '''
        3d plot of pixels color values

        some arg's are for interactive-manipulation +interproc-comm

        dictData - [dict] where each key has a value of a list of bgr lists.
        listColors = [list] of '#00ff00'-style color strings
                     of len equal to listB
        spaceTotal - [bool] if True, whole support of each axis
                    is displayed: 0 to 255
        spaceDefined - [dict] with keys 'x', 'y', 'z' and a tuple 
                     corresponding to (lo, hi) values on that axis
        viewPositionDefined - [dict] with keys elevation and azimuth
                        that dictate an initial view position
        regionMarkers - if not None, list of list 
        bInitPosition - [bool] set view-poisition when plt'd
        keyPressEvent - if not None, a reference to a function that
                        accepts a keyEvent arg and 
        axData -        if not None, a reference to a class instance method 
                        that attaches a reference to ax instance of a fig 

        TODOS
            [ ] do a second plot plt.scatter() ?
            [ ] title uses spaceDefined / spaceTotal inputs
    '''
    
    plt.close()     #reset from previous interactive
    
    fig = plt.figure()
    
    ax = fig.add_subplot(111, projection='3d')
    
    if ((len(viewPoisitonDefined.keys()) > 0) and
        bInitPosition):
    
        ax.view_init(azim = viewPoisitonDefined.get('azimuth')
                    ,elev = viewPoisitonDefined.get('elevation')
        )
        
    ax.scatter(xs=listB, ys=listG, zs=listR, c=listColors, marker='o')

    if len(dictData.keys()) > 0:
        for _k in dictData.keys():
            ax.scatter(*dictData[_k], c = 'red' ,marker = _k)

    if regionMarkers is not None:
        ax.scatter(xs=regionMarkers[0], ys=regionMarkers[1], zs=regionMarkers[2], 
                    c='black', marker='^')

    if axData is not None:
        axData(ax)

    if keyPressFunc is not None:
        fig.canvas.mpl_connect('key_press_event', keyPressFunc)

    
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
        
    if regionMarkers is not None:
        pass        #TODO

    ax.set_xlabel('B')
    ax.set_ylabel('G')
    ax.set_zlabel('R')

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
                ,dictData = {}
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
        self.dictData = dictData
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
        
        viewPoisitonDefined = {}
        keyPressSubproc = None
        setAxData = None

        if bInitPosition:
            viewPoisitonDefined['azimuth'] = self.azimuth
            viewPoisitonDefined['elevation'] = self.elevation
            
        if bInteractive:
            keyPressSubproc =  self.keyPressSubproc
            setAxData = self.setAxData
        
        colorCube(
                  listB = self.listB
                 ,listG = self.listG
                 ,listR = self.listR
                 ,listColors = self.listColors
                 ,dictData = self.dictData
                 ,spaceTotal = self.spaceTotal
                 ,spaceDefined = self.spaceDefined
                 ,viewPoisitonDefined  = viewPoisitonDefined
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
                 listB
                ,listG
                ,listR
                ,listColors = None
                ,dictData = {}
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
                ,dictData = dictData
                ,spaceTotal = spaceTotal
                ,spaceDefined = spaceDefined
                ,regionMarkers = regionMarkers
                ,dbPathFn = dbPathFn
                )
    
    subprocClass.save()

    #PROBLEM: matplotlib doesn't output when called from jupyter
        # running subprocess calling colorCube
        # <Figure size 640x480 with 1 Axes>



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
            


