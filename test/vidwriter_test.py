import os, sys, copy, cv2
sys.path.append("../")
from modules.vidwriter import VidWriter


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