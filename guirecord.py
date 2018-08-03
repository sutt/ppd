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
Globals.gui_unique_fn = "------N/A------"
Globals.gui_dir_path = "/"
Globals.sw_record_start = False
Globals.sw_record_stop = False
Globals.sw_gui_dir = False

try:
    gui = GuiB(b_log=True)
except Exception as e:
    print 'failed to start guiB'
    print e
    sys.exit()


while(not(Globals.gui_cmd_quit)):


    #SET VARS from GUI

    init_savedir = "data/aug2018/misc/"
    ext = "avi"
    b_codec = False   #True to do manual select popup
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

    #set directory to gui ang global
    gui.myGui.set_sv_dir(init_savedir)
    gui.myGui.get_sv_dir()

    fn = uniqueFn(  fn_base = "output"
                    ,fn_dir = Globals.gui_dir_path
                    ,fn_ext = ext
                    )
    
    gui.myGui.set_sv_fn(fn)
    gui.myGui.get_sv_fn()

    #TODO - move this to vidwrite block
    fourcc = -1 if b_codec else cv2.VideoWriter_fourcc("X","2","6","4") 
    
    t0 = time.time()
    i = 0
    while(cam.isOpened()):
            
        try:
            
            t_frame_i = time.time()
            
            ret,frame = cam.read()
            
            if ret:

                if b_logfps:
                    i += 1

                if b_show:
                    cv2.imshow('frame',frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                    #TODO - add destroyWindow for preveiw off

                if b_showsize:
                    print frame.shape

                if Globals.gui_cmd_record:

                    if Globals.sw_record_start:

                        Globals.sw_record_start = False

                        i = 0

                        fn = uniqueFn(  fn_base = "output"
                                        ,fn_dir = Globals.gui_dir_path
                                        ,fn_ext = ext
                                        )

                        if Globals.gui_unique_fn != fn:
                            fn = Globals.gui_unique_fn

                        out = VidWriter( 
                                 savefn = Globals.gui_dir_path + fn
                                ,fourcc = fourcc
                                ,outshape = frame_size
                                )
 
                        continue

                    out.write(frame)

                #TODO - add off switch in jumpcut vidwriter
                if Globals.sw_record_stop:

                    Globals.sw_record_stop = False
                    
                    out.release()

                    new_fn = uniqueFn(   fn_base = "output"
                                        ,fn_dir = Globals.gui_dir_path
                                        ,fn_ext = ext
                                        )
                    
                    gui.myGui.set_sv_fn(new_fn)
                    gui.myGui.get_sv_fn()

                if Globals.sw_gui_dir:
                    
                    Globals.sw_gui_dir = False

                    gui.myGui.get_sv_dir()

                    new_fn = uniqueFn(   fn_base = "output"
                                        ,fn_dir = Globals.gui_dir_path
                                        ,fn_ext = ext
                                        )
                    
                    gui.myGui.set_sv_fn(new_fn)
                    gui.myGui.get_sv_fn()



            if (time.time() - t0) > time_to_record:
                break

            if Globals.gui_cmd_quit:
                break
        
        except Exception as e:
            print 'excepted during frame read.'
            print e
            break


#Clean up        
try:
    cam.release()
except:
    print 'no cam to release'

try:
    out.release()
except:
    print 'no out to release'

try:
    cv2.destroyAllWindows()
except:
    print 'no cv2 windows to destroy'
    
try:
    if b_save:
        pfn = str(Globals.gui_dir_path) + fn
        print pfn, ": ", str(os.path.getsize(pfn) / (1000)), " kb"
except:
    print 'couldnt find most recent saved file.'