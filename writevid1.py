import numpy as np
import cv2
import argparse
import os, sys, time
from miscutils import uniqueFn
from vidwriter import VidWriter

'''
EXAMPLES
>python writevid1.py            (basic, record a video for 5 seconds)
>python writevid1.py --time 10 --savedir data/aug2018/misc/
>python writevid1.py --framesize 1280,720
>python writevid1.py --framesize 1920,1080
>python writevid1.py --logfps   (print each frame and )
>python writevid1.py --dryrun
    (dryrun dont record the video)
>python writevid1.py --bcodec
    (bcodec creates a windows prompt of vid-save-codec choice)


TODOS
[x] why not prompt for -1 ?
[x] dont check file when not saving
[ ] add a gui   
[ ] add a help page
[ ] do a preview and have a start/stop button
[ ] use logfps for easy start logging vid-info
[ ] warmup time
[ ] store meta-data
[ ] write/log meta-data
    maybe we store vidname as (short) guid and then thats the 
    primary key for meta-data lookup 
    short guid as opposed to date time helps with CLI input
[ ] better default on save directory
[ ] add a way to add notes meta-data e.g. "green ball, poor lighting"
'''


def main(    
             time_to_record = 5
            ,cam_num = 0
            ,frame_size = (640,480)
            ,savedir = ""
            ,ext = ""
            ,b_codec = False
            ,b_save = True
            ,b_show = False
            ,b_logfps = False
            ,b_showsize = False
        ):
    '''
        Record a Video, and Save to Disk.
    '''

    if b_save:

        #TODO - input_fn
        
        fn = uniqueFn(  fn_base = "output"
                        ,fn_dir = savedir
                        ,fn_ext = ext
                        )

        fourcc = -1 if b_codec else cv2.VideoWriter_fourcc("X","2","6","4") 

        out = VidWriter( savefn = savedir + fn
                        ,fourcc = fourcc
                        ,outshape = frame_size
                        )


    cam  =  cv2.VideoCapture(cam_num)

    if frame_size != (640,480):
        try:
            cam.set(3,frame_size[0])
            cam.set(4,frame_size[1])
        except:
            print 'couldnt set cam with frame_size: ', str(frame_size)


    t0 = time.time()
    i = 0

    while(cam.isOpened()):
            
        try:
            
            t_frame_i = time.time()
            
            ret,frame = cam.read()
            
            if ret:

                if b_showsize:
                    print frame.shape
            
                if b_save:
                    out.write(frame)

                if b_logfps:
                    i += 1
                
                if b_show:
                    cv2.imshow('frame',frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

            if (time.time() - t0) > time_to_record:
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
        
    if b_save:
        pfn = str(savedir) + fn
        print pfn, ": ", str(os.path.getsize(pfn) / (1000)), " kb"

    if b_logfps:
        print 'numFrames recorded = ', str(i)



if __name__ == "__main__":
    
    #ARGS
    ap = argparse.ArgumentParser()
    ap.add_argument("--showvid", action="store_true", default=False)
    ap.add_argument("--showsize", action="store_true", default=False)
    ap.add_argument("--dryrun", action="store_true", default=False)
    ap.add_argument("--logfps", action="store_true", default=False)
    ap.add_argument("--framesize", type=str, default="")
    ap.add_argument("--bcodec", action="store_true", default=False)
    ap.add_argument("--codec", type=str, default="h264")
    ap.add_argument("--ext", default = "avi")
    ap.add_argument("--savedir", default="data/july2018/misc/")
    ap.add_argument("--time",  default=5)
    ap.add_argument("--camnum", type=str, default=0)
    args = vars(ap.parse_args())

    #PARSE
    if args["framesize"] != "":    
        try:
            str_frame_size = str(args["framesize"])
            split_frame_size = str_frame_size.split(",")
            frame_size = tuple(map(int,split_frame_size[:2]))
        except:
            frame_size = (640,480)
            print 'couldnt parse framesize argument'
    else:
        frame_size = (640,480)

    #MAIN
    main( 
             time_to_record = int(args["time"])
            ,cam_num =      args["camnum"]
            ,frame_size =   frame_size
            ,savedir =      args["savedir"]
            ,ext =          args["ext"]
            ,b_codec =      args["bcodec"]
            ,b_save =       not(args["dryrun"])
            ,b_show =       args["showvid"]
            ,b_logfps =     args["logfps"]
            ,b_showsize =   args["showsize"]
        )

def test_unit_1():
    pass