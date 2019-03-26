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


def test_vidwriter_basic_1():
    
    #TODO - get MP4 format to work
    #TODO - get rid of prompt for codec, must specify fourcc

    import os

    input_staging_dir = "../data/test/vidwriter/input/"
    output_staging_dir = "../data/test/vidwriter/output/"
    
    #Setup
    output_files = os.listdir(output_staging_dir)
    for output_file in output_files:
        os.remove(output_staging_dir + output_file)
    assert len(os.listdir(output_staging_dir)) == 0

    NUM_IMGS = 3
    input_fns = [ input_staging_dir + "testimg" + str(i) + ".jpg"
                  for i in range(NUM_IMGS)
                ]
    input_imgs = [cv2.imread(input_fns[i])
                    for i in range(NUM_IMGS)
                 ]
    assert len(input_imgs) == NUM_IMGS

    for i in range(NUM_IMGS):
        assert input_imgs[i].shape == (480,640,3)

    #Actions
    
    # A window-popup prompt, removed for automated run
    # fn = output_staging_dir + "testvid.avi"
    # vw = VidWriter(fn)
    # for i in range(NUM_IMGS):
    #     vw.write(input_imgs[i])
    # vw.release()

    fn = output_staging_dir + "testvid.h264"
    vw = VidWriter(fn, fourcc = "h264")
    for i in range(NUM_IMGS):
        vw.write(input_imgs[i])
    vw.release()

    fn = output_staging_dir + "testvid.mp4"
    vw = VidWriter(fn, fourcc = "mp4")
    for i in range(NUM_IMGS):
        vw.write(input_imgs[i])
    vw.release()

    fn = output_staging_dir + "testfourcc.h264"
    my_fourcc = cv2.VideoWriter_fourcc("X","2","6","4")
    vw = VidWriter(fn, fourcc = my_fourcc)
    for i in range(NUM_IMGS):
        vw.write(input_imgs[i])
    vw.release()

    fn = output_staging_dir + "testext"
    vw = VidWriter(fn, fourcc = "h264", ext="h264")
    for i in range(NUM_IMGS):
        vw.write(input_imgs[i])
    vw.release()

    fn = output_staging_dir + "testext.2"
    vw = VidWriter(fn, ext="avi", fourcc ="h264" )
    for i in range(NUM_IMGS):
        vw.write(input_imgs[i])
    vw.release()

    fn = output_staging_dir + "testlossless"
    vw = VidWriter(fn, ext="avi", fourcc = 0 )
    for i in range(NUM_IMGS):
        vw.write(input_imgs[i])
    vw.release()
    
    
    #Verify
    output_files = os.listdir(output_staging_dir)
    # assert "testvid.avi" in output_files
    assert "testvid.h264" in output_files
    # assert "testvid.mp4" in output_files
    assert "testfourcc.h264" in output_files
    assert "testext.h264" in output_files
    # assert "testext.2.avi" in output_files

    # fn = output_staging_dir + "testvid.avi"
    # assert os.path.getsize(fn) > 0
    fn = output_staging_dir + "testvid.h264"
    assert os.path.getsize(fn) > 0
    # fn = output_staging_dir + "testvid.mp4"
    # assert os.path.getsize(fn) > 0
    fn = output_staging_dir + "testfourcc.h264"
    assert os.path.getsize(fn) > 0
    fn = output_staging_dir + "testext.h264"
    assert os.path.getsize(fn) > 0
    fn = output_staging_dir + "testext.2.avi"
    assert os.path.getsize(fn) > 0
    fn = output_staging_dir + "testlossless.avi"
    assert os.path.getsize(fn) > 0

