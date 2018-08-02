import numpy as np
import cv2
import argparse
import os, sys, time
from writevid1 import main
from miscutils import uniqueFn
from vidwriter import VidWriter
import modules.GlobalsB as Globals
from modules.GuiB import GuiB


'''

DATA EXCHANGE 
Cam I/O <-> VideoRecord <-> GUI I/O <-> (meta-data DB) & FileSystem

admin gui cmds:
    quit
    record/stop
    time_to_record
    filename
    show video

Cam settings
    framesize
    Transforms on frames
        (different than transforms on compressed frames and vid)
    Gain
    ISO
    what was set away from default?
    

indv. video data:
    timing of each frame
    avg FPS
        numFrames
        recordTime (ms)
    text notes




'''

Globals.init()
Globals.gui_cmd_quit = False
Globals.gui_cmd_record = False
Globals.gui_cmd_reset = False

try:
    gui = GuiB()
except Exception as e:
    print 'failed to start guiB'
    print e
    sys.exit()


while(not(Globals.gui_cmd_quit)):


    #SET VARS from GUI

    savedir = "data/aug2018/misc/"
    ext = "avi"
    b_codec = False
    frame_size = (640,480)
    cam_num = 0
    input_fn = None
    time_to_record = 99
    b_logfps = False
    b_show = True
    b_save = True
    b_showsize = False


    #INIT NEW VIDEO

    cam  =  cv2.VideoCapture(cam_num)

    if frame_size != (640,480):
        try:
            cam.set(3,frame_size[0])
            cam.set(4,frame_size[1])
        except:
            print 'couldnt set cam with frame_size: ', str(frame_size)

    if Globals.gui_cmd_reset:
        break
    

    #SAVE-FN INIT------------------------------------------------
    fn = uniqueFn(  fn_base = "output"
                    ,fn_dir = savedir
                    ,fn_ext = ext
                    )
               
    if input_fn != "" and input_fn is not None:
        fn = input_fn
        #TODO - validate its unqiue in the directory

    fourcc = -1 if b_codec else cv2.VideoWriter_fourcc("X","2","6","4") 

    #TODO - don't init vidwriter yet
    out = VidWriter( savefn = savedir + fn
                    ,fourcc = fourcc
                    ,outshape = frame_size
                    )
    # -------------------------------------------------------------

    #RECORD VIDEO
    
    t0 = time.time()
    i = 0
    while(cam.isOpened()):
            
        try:
            
            t_frame_i = time.time()
            
            ret,frame = cam.read()
            
            if ret:

                if b_show:
                    cv2.imshow('frame',frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                if b_showsize:
                    print frame.shape

                if Globals.gui_cmd_record:
                    out.write(frame)

                if b_logfps:
                    i += 1
                
                

            if (time.time() - t0) > time_to_record:
                break

            if Globals.gui_cmd_quit:
                break
        
        except:
            print 'excepted during frame read.'
            break


#Clean up        
cam.release()
try:
    out.release()
except:
    print 'no out to release'

try:
    cv2.destroyAllWindows()
except:
    print 'no cv2 windows to destroy'
    
    
if b_save:
    pfn = str(savedir) + fn
    print pfn, ": ", str(os.path.getsize(pfn) / (1000)), " kb"