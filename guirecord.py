import numpy as np
import cv2
import argparse
import os, sys, time
from writevid1 import main
from miscutils import uniqueFn
from vidwriter import VidWriter
import modules.GlobalsB as Globals
from modules.GuiB import GuiB
from modules.GraphicsCV import resize_img
from modules.Utils import TimeLog

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
Globals.gui_b_jumpcut = False
Globals.b_jumpcut_inprogress = False
Globals.sw_preview_frame = False
Globals.gui_b_preview_frame = True
Globals.sw_camera_reset = False
Globals.gui_frame_size_enum = 0
Globals.gui_cam_num = 0
Globals.gui_b_resize = True
Globals.gui_codec_enum = 0
Globals.gui_b_buffer = False
Globals.gui_log_enum = 0


try:
    gui = GuiB(b_log=True)
except Exception as e:
    print 'failed to start guiB'
    print e
    sys.exit()


while(not(Globals.gui_cmd_quit)):

    Globals.sw_camera_reset = False

    
    init_savedir = "data/sept2018/misc/"
    ext = "avi"
    time_to_record = 99
    b_show = True
    reset_cntr_exit = 10
    list_frames = []
    reset_cntr = 0
    sw_outofmem_break = False
    

    
    if Globals.gui_log_enum == 0:
        #simple
        b_timelog = True    
        b_log_vars = False  
    if Globals.gui_log_enum == 1:
        #detailed
        b_timelog = True   
        b_log_vars = True
    if Globals.gui_log_enum == 2:
        #none
        b_timelog = False   
        b_log_vars = False

    timelog = TimeLog(inert = not(b_timelog)
                     ,b_log_vars = b_log_vars
                     )
    
    if Globals.gui_frame_size_enum == 0:
        frame_size = (640,480)
    if Globals.gui_frame_size_enum == 1:
        frame_size = (1280,720)
    if Globals.gui_frame_size_enum == 2:
        frame_size = (1920,1080)        

    if Globals.gui_codec_enum == 0:
        fourcc = cv2.VideoWriter_fourcc("X","2","6","4")
    if Globals.gui_codec_enum == 1:
        fourcc = -1   
    if Globals.gui_codec_enum == 2:
        fourcc = 0   

    cam  =  cv2.VideoCapture(Globals.gui_cam_num)

    try:
        cam.set(3,frame_size[0])
        cam.set(4,frame_size[1])
    except:
        print 'couldnt set cam with frame_size: ', str(frame_size)


    gui.myGui.set_sv_dir(init_savedir)      #set directory to gui ang global
    gui.myGui.get_sv_dir()

    fn = uniqueFn(  fn_base = "output"
                    ,fn_dir = Globals.gui_dir_path
                    ,fn_ext = ext
                    )
    
    gui.myGui.set_sv_fn(fn)
    gui.myGui.get_sv_fn()
    
    t0 = time.time()
    reset_cntr += 1

    while(cam.isOpened()):
            
        try:
            
            timelog.log_start()

            ret,frame = cam.read()

            timelog.log_time( 
                              Globals.gui_cmd_record
                             ,Globals.gui_b_preview_frame
                             ,Globals.gui_frame_size_enum
                            )
            
            if ret:

                if Globals.sw_preview_frame:
                    
                    Globals.sw_preview_frame = False
                    
                    if b_show:
                        b_show = False
                        cv2.destroyAllWindows()
                    else:
                        b_show = True
                
                if b_show:
                    if Globals.gui_b_resize:
                        img_display = frame.copy()
                        img_display = resize_img(frame, True)    
                        cv2.imshow('img_display',img_display)
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break
                    else:
                        cv2.imshow('unresized_frame',frame)
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break
                    

                if Globals.gui_cmd_record:

                    if Globals.sw_record_start:

                        Globals.sw_record_start = False

                        if Globals.gui_b_jumpcut:
                            if Globals.b_jumpcut_inprogres:
                                continue

                        if not(Globals.gui_b_jumpcut):
                            Globals.b_jumpcut_inprogres = False
                            try:
                                out.release()
                            except:
                                pass

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

                        timelog.set_output(Globals.gui_dir_path + fn)

                        if Globals.gui_b_jumpcut:
                            Globals.b_jumpcut_inprogres = True
 
                        continue
                    
                    if Globals.gui_b_buffer:
                        list_frames.append(frame.copy())
                    else:
                        out.write(frame)

                
                if Globals.sw_record_stop:

                    Globals.sw_record_stop = False
                                  
                    if Globals.gui_b_jumpcut:
                        continue
                    
                    timelog.output_log()

                    if Globals.gui_b_buffer:
                        for _frame in list_frames:
                            out.write(_frame)
                        list_frames = []

                        if sw_outofmem_break:
                            #you broke from outof meme: continue writing another file
                            sw_outofmem_break = False
                            Globals.sw_record_start = True
                        else:
                            #you broke my hitting record button: pause on gui and dont save
                            gui.myGui.cmd_record_sw()
                            Globals.gui_cmd_record = False

                    out.release()

                    new_fn = uniqueFn(   fn_base = "output"
                                        ,fn_dir = Globals.gui_dir_path
                                        ,fn_ext = ext
                                        )
                    
                    gui.myGui.set_sv_fn(new_fn)
                    gui.myGui.get_sv_fn()

                if Globals.sw_gui_dir:
                    
                    Globals.sw_gui_dir = False

                    new_fn = uniqueFn(   fn_base = "output"
                                        ,fn_dir = Globals.gui_dir_path
                                        ,fn_ext = ext
                                        )
                    
                    gui.myGui.set_sv_fn(new_fn)
                    gui.myGui.get_sv_fn()


            if Globals.gui_b_buffer:

                if sys.getsizeof(frame)* len(list_frames) > 1.5 * (10**9):    
                    Globals.sw_record_stop = True
                    sw_outofmem_break = True

                if reset_cntr > reset_cntr_exit:
                    break

            
            if (time.time() - t0) > time_to_record:
                break

            if Globals.gui_cmd_quit:
                break

            if Globals.sw_camera_reset:
                break
        
        except Exception as e:
            print 'excepted during frame read.'
            print e
            break

    #Exit one cam-setup loop; still in main gui-loop
    try:
        cam.release()
    except:
        print 'no cam to release'

    try:
        out.release()
    except:
        print 'no out to release'

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
    pfn = str(Globals.gui_dir_path) + fn
    print pfn, ": ", str(os.path.getsize(pfn) / (1000)), " kb"
except:
    print 'couldnt find most recent saved file.'