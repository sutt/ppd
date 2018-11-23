import copy, random, subprocess
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from modules.Interproc import GuiviewState
from modules.ControlTracking import TrackFactory
from modules.ControlDisplay import Display

'''
    functions to use in jupyter notebooks to debug different
    trackers under different scenarios

    TODOs
        [ ] inWindowCheck() returns True if trackScuess and center is
            in window
        [ ] add unit tests
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
    return [
        "#" + hex(x[0])[2:] + hex(x[1])[2:] + hex(x[2])[2:]
        for x in zip(listR, listG, listB)
    ]



def colorPlot(listB, listG, listR
               ,listColors = None
               ,spaceTotal = True
               ,spaceDefined = {}
               ,regionMarkers = None
              ):
    '''
        3d plot of pixels color values

        listColors = [list] of '#00ff00'-style color strings
                     of len equal to listB
        spaceTotal - [bool] if True, whole support of each axis
                    is displayed: 0 to 255
        spaceDefined - [dict] with keys 'x', 'y', 'z' and a tuple 
                     corresponding to (lo, hi) values on that axis
        regionMarkers - TODO 

        TODOS
            [ ] do a second plot plt.scatter() ?
            [ ] title uses spaceDefined / spaceTotal inputs
    '''
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(xs=listB, ys=listG, zs=listR, c=listColors)
    
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
        pass
        #TODO

    ax.set_xlabel('B')
    ax.set_ylabel('G')
    ax.set_zlabel('R')
    
    plt.show()


def subprocColorPlot():
    '''
        3d color plot as subprocess; allows good interactivity when
        called from jupyter but using a true TK window outside browser/
    '''
    pass


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
    
    fig.show()