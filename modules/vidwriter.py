import cv2
import types

def VidWriter(savefn
              ,fourcc=None
              ,outfps=None
              ,outshape=None
              ,ext=None
            ):
    '''
        return a cv2 VideoWriter Object

        savefn:     relative path to save directory
        fourcc:     VideoWriter_fourcc or string
        outfps:     int
        outshape:   (w,h)
        ext:        str, if used will append to filename

        vw = VidWriter( savefn = args["savedir"] + fn
                        ,fourcc = args["codec"])
    '''
    
    if fourcc is None:
        _fourcc = -1    #change from prompt
    
    elif type(fourcc) == types.StringType:
        
        if str.lower(fourcc) in ("h264", "x264"):
            _fourcc = cv2.VideoWriter_fourcc("X","2","6","4")
        elif str.lower(fourcc) == "mp4":
            #TODO - get this to work
            _fourcc = cv2.VideoWriter_fourcc("M","P","4"," ")
        else:
            try:
                c = [fourcc[i] if len(fourcc) >= i else " "
                        for i in range(3)
                    ]
                _fourcc = cv2.VideoWriter_fourcc(c[0],c[1],c[2],c[3])
            except:
                print 'fourcc type ', str(fourcc), ' not recognized.'
                _fourcc = -1

        # fourcc = cv2.VideoWriter_fourcc(*'XVID')

    else:
        _fourcc = fourcc
    
    if outfps is None:
        _outfps = 30
    else:
        _outfps = outfps

    if fourcc == 0:
        _outfps = 0     #lossless

    if outshape is None:
        _outshape = (640,480)
    else:
        _outshape = outshape

    if ext is None:
        _savefn = savefn
    else:
        _savefn = savefn + "." + ext

    return cv2.VideoWriter(_savefn,_fourcc,_outfps,_outshape)    




