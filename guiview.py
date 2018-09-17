import numpy as np
import cv2
import argparse
import os, sys, time
from writevid1 import main
from miscutils import uniqueFn
from vidwriter import VidWriter
import modules.GlobalsC as g
from modules.GuiC import GuiC
from modules.GraphicsCV import resize_img
from modules.Utils import TimeLog
from modules.Utils import MetaDataLog
from modules.GraphicsCV import draw_annotations, resize_img
'''

'''

g.init()
g.gui_cmd_quit = False
g.gui_cmd_record = False
g.gui_cmd_reset = False
g.gui_unique_fn = "------N/A------"
g.gui_dir_path = "/"
g.sw_record_start = False
g.sw_record_stop = False
g.sw_gui_dir = False
g.gui_b_jumpcut = False
g.b_jumpcut_inprogress = False
g.sw_preview_frame = False
g.gui_b_preview_frame = True
g.sw_camera_reset = False
g.gui_frame_size_enum = 0
g.gui_cam_num = 0
g.gui_b_resize = True
g.gui_codec_enum = 0
g.gui_b_buffer = False
g.gui_log_enum = 0

g.playOn = True


ap = argparse.ArgumentParser()
ap.add_argument("--nogui",  action="store_true", default=False)
ap.add_argument("--dir", type=str, default="")
args = vars(ap.parse_args())

if not(args["nogui"]):
    gui = GuiC(b_log=True)  

if args["dir"] == "":
    b_play_dir = False
    b_preload = True
    init_dir = "data/proc/hello-training-data/"
else:
    b_play_dir = True
    b_preload = False
    init_dir = args["dir"]
    b_annotate_fn = True
    b_resize = True


if b_play_dir:
    list_files = os.listdir(init_dir)
    list_vids = filter(lambda fn: ".avi" in fn, list_files)

play_counter = 0

while(True):

    FN = "output4"
    EXT = "avi"
    
    vidFn = (FN + "." + EXT)

    if b_play_dir:
        vidFn = list_vids[play_counter % len(list_vids)]

    cam = cv2.VideoCapture(os.path.join(init_dir, vidFn))

    
    
    play_counter += 1

    if b_preload:
        preloaded_frames = preloadFromCam()

    while(cam.isOpened()):

        ret,frame = cam.read()

        refresh = 1 if (g.playOn) else 5000

        if ret:

            #TODO - copy / annotate / resize
            img_display = frame.copy()

            if b_resize:
                img_display = resize_img(img_display, True, (640,480))
            
            if b_annotate_fn:
                info_annotations = [vidFn]
                img_display = draw_annotations(img_display, info_annotations)


            cv2.imshow('img_display', img_display)
            if cv2.waitKey(refresh) & 0xFF == ord('q'):
                break

        else:
            
            cam.release()

        #TODO - delay frame


cv2.destroyAllWindows()