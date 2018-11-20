from matplotlib import pyplot as plt
from modules.Interproc import GuiviewState
from modules.ControlTracking import TrackFactory

'''
    functions to use in jupyter notebooks to debug different
    trackers under different scenarios

    TODOs
        [ ] inWindowCheck() returns True if trackScuess and center is
            in window
        [ ] add unit tests
'''

def applyTracker(listGS, tracker, roiSelectFunc = None):
    ''' 
        pass in:
         listGS -  list of GuiviewState objs; "states"
         tracker - one trackFactory obj; applied to all states
         roiSelectFunc - a function that takes a guiviewstate obj
                    as an argument, and returns an image

        returns dict:
         listScore - list of ScoreSchema obj's; one for each state
         listPlts - list of list of np.arrays (or None) representing
                    an image within the trackAlgo pipeline. 
                    outer list: one for each state
                    inner list: one for each transform in trackAlgo
         listTransformTitles - list of variable names corresponding to
                    img transforms within trackAlgo
         listFrameTitles - list of frame-indexes
        
        TODOs
        [x] better name
        [x] better description
        [x] arg for window selection
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