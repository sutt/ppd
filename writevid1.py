import numpy as np
import cv2
import argparse
import os, sys, time
from miscutils import uniqueFn
from vidwriter import VidWriter

'''
TODOS
[ ] change frame size
[ ] do a preview and have a start/stop button
[ ] store meta-data
[ ] write/log meta-data
    maybe we store vidname as (short) guid and then thats the 
    primary key for meta-data lookup 
    short guid as opposed to date time helps with CLI input
[ ] better default on save directory
[ ] add a way to add notes meta-data e.g. "green ball, poor lighting"
[x] insert unqiueFn and VidWriter
[x] change savedir
'''


ap = argparse.ArgumentParser()
ap.add_argument("--showvid", action="store_true", default=False)
ap.add_argument("--showsize", action="store_true", default=False)
ap.add_argument("--dontsave", action="store_false", default=True)
ap.add_argument("--dontrecord", action="store_false", default=True)
ap.add_argument("--getcam", action="store_true", default=False)
ap.add_argument("--setcam", action="store_true", default=False)
ap.add_argument("--setgain", action="store_true", default=False)
ap.add_argument("--logfps", action="store_true", default=False)
ap.add_argument("--toggleframe", action="store_true", default=False)

ap.add_argument("--codec", default="h264")
ap.add_argument("--ext", default = "avi")

ap.add_argument("--savedir", default="data/july2018/misc/")
	
ap.add_argument("--time",  default=3)

args = vars(ap.parse_args())

time_to_record = int(args["time"])
#Video Options

cd = args["codec"]
if  cd == "" :
    fourcc = -1
else:
    # fourcc = cv2.VideoWriter_fourcc(cd[0],cd[1],cd[2],cd[3])
    # fourcc = cv2.VideoWriter_fourcc("M","P","4"," ")
    fourcc = cv2.VideoWriter_fourcc("X","2","6","4")
    #Logitech Video I420 works
    #default:-466162819.0
    #divx, xvid, h264, x264, mjpg, wmv?
    

_fw = cv2.CAP_PROP_FRAME_WIDTH 
_fh = cv2.CAP_PROP_FRAME_HEIGHT
_fps = cv2.CAP_PROP_FPS
_fourcc = cv2.CAP_PROP_FOURCC

_params = [_fw,_fh,_fps,_fourcc]

if args["setcam"]:
    # outshape = (1920,1080)
    outshape = (1080,960)
    outfps = 30
else:
    outshape = (640,480)
    outfps = 30
    

#WriteVideo
if args["dontsave"]:

    fn = uniqueFn(  fn_base = "output"
                    ,fn_dir = args["savedir"]
                    ,fn_ext = args["ext"]
                    )
    print fn
    out = VidWriter( savefn = args["savedir"] + fn
                    ,fourcc = args["codec"]
                    )


#Caemra Object            
cam  =  cv2.VideoCapture(0)

if args["getcam"]:
    _cam = [cam.get(p) for p in _params]
    print _cam

if args["setcam"]:
    
   # First set codec, then fps, then h/w #http://stackoverflow.com/questions/16092802/capturing-1080p-at-30fps-from-logitech-c920-with-opencv-2-4-3
    if args["toggleframe"]:
        try:
            rrr,fff = cam.read()
        except:
            print 'couldnt toggle'
        
    #cam.set(_fourcc,fourcc)
    
    #cam.set(_fourcc,cam.get(_fourcc))
    #_I420 2304,1536, fps=2
    #cam.set(_fps,30)
    
    cam.set(_fw,outshape[0])
    cam.set(_fh,outshape[1])
    
    _cam = [cam.get(p) for p in _params]
    print _cam

if args["setgain"]:
    cam.set(cv2.CAP_PROP_GAIN,255)
    print cam.get(cv2.CAP_PROP_GAIN)
    cam.set(cv2.CAP_PROP_EXPOSURE,-5)
    print cam.get(cv2.CAP_PROP_EXPOSURE)
    cam.set(cv2.CAP_PROP_BRIGHTNESS,128)
    print cam.get(cv2.CAP_PROP_BRIGHTNESS)
    
#Record Video
if args["dontrecord"]:

    a = time.time()
    i = 0
    while(cam.isOpened()):
        
        
        try:
            a2 = time.time()
            ret,frame = cam.read()
            
            if ret:

                if args["showsize"]:
                    print frame.shape
            
                if args["dontsave"]:
                    out.write(frame)

                if args["showvid"]:
                    cv2.imshow('frame',frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                if args["logfps"]:
                    #print float(1.0) / float(time.time() - a2)
                    i += 1
                
            if (time.time() - a) > time_to_record:
                print 'done with i = ', str(i)
                break
        except:
            print 'excepted'
            break

#Clean up        
cam.release()
try:
    out.release()
except:
    print 'no out to release'
    
pfn = str(args["savedir"]) + fn
print pfn, ": ", str(os.path.getsize(pfn) / (1000)), " kb"
