import os, sys, time, copy, random, argparse
import traceback
import numpy as np
import cv2
import imutils
from collections import deque
from matplotlib import image as mpimg
from matplotlib import pyplot as plt

from track_a import find_xy, find_radius
from GraphicsA import LiveHist

ap = argparse.ArgumentParser()
ap.add_argument("--file", type=str, default="fps30.h264")
ap.add_argument("--showhisto", action="store_true")
ap.add_argument("--showbackghisto", action="store_true")
ap.add_argument("--printlog", action="store_true")
args = vars(ap.parse_args())

def px3clr_3px1clr(list_pixels):
    return [ map( lambda v: v[clr], list_pixels ) for clr in range(3)]

def px_to_list(img):
    hL,wL = img.shape[0], img.shape[1]  
    return [ tuple( img[h,w,:] ) for h in range(hL) for w in range(wL) ]
            
def px_remove_crop(img, crop_params ):
    x0,y0 = crop_params[0]
    x1,y1 = crop_params[1]
    hL,wL,cL = img.shape
    return [ tuple( img[h,w,:] ) for h in range(hL) for w in range(wL) 
                if ((h < y0) or (h > y1)) and
                   ((w < x0) or (w > x1)) ]

def hist_from_img(inp_img):
    list_px = px_to_list(inp_img)
    on_pxs = px3clr_3px1clr(list_px)
    return on_pxs


def transformA(img, blur = 11, b_hsv = False):
    #frame = imutils.resize(frame, width=600)
    out = cv2.GaussianBlur(img, (blur, blur), 0)
    if b_hsv: return cv2.cvtColor(out, cv2.COLOR_BGR2HSV)
    return out    
    

def threshA(img, threshLo = (0,0,0), threshHi = (255,255,255)):
    return cv2.inRange(img, threshLo, threshHi)
    
def repairA(img, iterations = 2):
    img = cv2.erode(img, None, iterations=iterations)
    img = cv2.dilate(img, None, iterations=iterations)
    return img

def crop_img(img, current_tracking_frame):
    x0,y0 = current_tracking_frame[0][0], current_tracking_frame[0][1]
    x1,y1 = current_tracking_frame[1][0], current_tracking_frame[1][1]
    return img[x0:x1,y0:y1,:]    

def draw_tracking_frame(img, x,y,radius):
    cv2.circle(img, (int(x), int(y)), int(radius), (0, 255, 255), 10)
    return img

def draw_tracking(img, rect ):
    cv2.rectangle(img, rect[0], rect[1], (0, 255, 255), 3)
    return img

def draw_annotations(img, info_annotations):
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img,'OpenCV',(10,10), font, 2,(255,255,255),2,cv2.LINE_AA)
    return img

def initCam(cam_type,**kwargs):
    if cam_type == 'cv_cam': 
            return cv2.VideoCapture(kwargs.get('usb_num',0) )
    elif cam_type == 'pi_cam': 
        return 1
    elif cam_type == 'file_cam': 
        return  cv2.VideoCapture(kwargs.get('vid_file'),'')
    else:
        print 'No cam object creatable.'

def setupCam(vc, cam_type, params):
    # set ISO, shutter speed, fps, etc...
    try:
        pass
    except Exception as e:
        print 'Could not set cam params: ', str(e)
        print traceback.format_exc()
    return vc

def getFrame(inp_cam, cam_type):
        if cam_type == 'cv_cam': 
            return inp_cam.read()
        elif cam_type == 'pi_cam': 
            return True, inp_cam
        elif cam_type == 'file_cam': 
            return inp_cam.read()
        else:
            print 'No frame read possible.'

def flip_img(img,flip = True):
    """return a non-copied image be default vertically flipped"""
    if flip:
        return cv2.flip(img,1)
    else:
        return img

def showImages(img_display,**kwargs):
    
    b_flip = not(kwargs.get('dont_mirror',False))

    if kwargs.get('b_show_main_img', False):
        cv2.imshow('display image'
                    ,flip_img(img_display, b_flip) )
    
    if kwargs.get('b_show_transformed_img', False):
        cv2.imshow('transformed image'
                    ,flip_img( kwargs.get('img_t',None), b_flip ) )
                    
    if kwargs.get('b_show_tracked_img', False):
        cv2.imshow('the ball',kwargs.get('on_pxs',None))

    if kwargs.get('b_show_mask_img', False):
        cv2.imshow('the ball',kwargs.get('img_m',None))

    return 0

def create_tracking_frame(**kwargs):
    return ((100,100),(300,300))

def mock_gaussian(n = 100, **kwargs ):
    z = np.random.randn(n)
    u, var = kwargs.get('u',0), kwargs.get('var',1)
    return map(lambda z_i: u + (z_i*var), z)
    
def rand_gauss_params():
    u = random.randint(0,255)
    var = random.randint(10,50)
    return u, var

def mock_hist_data():
    u, var = rand_gauss_params()
    hist_data = map( lambda x: mock_gaussian(n=100,u=u,var=var), range(3) )
    return hist_data

def main():

    #Init and Params ---------------------------
    cam_params = (640,480)
    h_img, w_img = cam_params[0], cam_params[1]
    cam_type = 'cv_cam'     # 'pi_cam' 'file_cam'
    
    current_tracking_frame = ((100,100),(200,200))

    b_tracking_frame = True
    b_tracking_frame_2 = False
    b_histo = args["showhisto"]     #takes 0.3 secs to process
    b_hist_rect = True
    b_show_histos = args["showhisto"]  #takes 0.3 secs to process
    b_show_backg_histos = args["showbackghisto"]
    b_mock_hist_data = False
    b_drawTracking = True
    b_print_log = args["printlog"]

    switch_new_ylim = True  #once, everytime new tracking frame is drawn
    ylim_padding_mult = 1.0

    hist_update_hz = 1
    waitKeyRefresh = 1

    time_last = time.time()
    info_annotations = []
    
    vc = initCam(cam_type)
    vc = setupCam(vc, cam_type = cam_type, params = cam_params)

    livehist = None


    while(vc.isOpened()):

        if b_print_log:
            print 'frame time: %.2f' % (time.time() - time_last)
            time_last = time.time()

        ret, frame = getFrame(vc, cam_type = 'cv_cam')        
        if not(ret): break

        if b_tracking_frame_2:
            current_tracking_frame = create_tracking_frame()
            img = crop_img(frame, current_tracking_frame)
        else:
            img = frame[:,:,:]

        # THRESHOLD MASK
        img_t = transformA(img, b_hsv = True)
        Lo, Hi = (29, 86, 6), (64, 255, 255)
        img_mask = threshA(img_t, threshLo = Lo , threshHi = Hi )
        img_mask = repairA(img_mask, iterations = 2)
        
        
        # LOCATE / TRACK
        x,y = find_xy(img_mask)
        radius = find_radius(img_mask)
        #print x, ' ', y, ' ', radius
        
        # if b_tracking_frame:
        #     x,y,radius = decrop_track(h_img, w_img)
        # b_track_success = filter_track()
        b_track_success = True


        #DRAW ONTO FRAME
        img_display = frame

        if b_tracking_frame:
            img_display = draw_tracking_frame(frame,x,y,radius)

        if b_drawTracking: # and b_track_success:
            img_display = draw_tracking(img_display,current_tracking_frame)

        b_annotate_img = False
        if b_annotate_img:
            img_display = draw_annotations(img_display, info_annotations)       
            

        # PROC & SHOW HISTOS
        if b_show_histos:
            
            if livehist == None:
                
                # INIT HISTO GUI
                if args["showbackghisto"]:
                    h,w = 2,3
                    NUM_PLOTS = 6
                else:
                    h,w = 1,3
                    NUM_PLOTS = 3

                livehist = LiveHist( h = h, w = w, bins = 30
                                    ,x_lo = -1, x_hi = 256
                                    ,y_lo = 0 ,y_hi = 7000 )
                
                livehist.show_plt(wait_time = 2)

                last_hist_update = time.time() - (hist_update_hz + 1)    #and process
                
            
            if time.time() - last_hist_update > hist_update_hz:

                # HISTO_PROCESSING
                if b_histo:
                    
                    rect_img = crop_img(frame.copy(), current_tracking_frame)
                    rect_list_px = px_to_list(rect_img)
                    hist_data_rect = px3clr_3px1clr(rect_list_px)
                    
                    backg_list_px = px_remove_crop(frame, current_tracking_frame)
                    hist_data_backg = px3clr_3px1clr(backg_list_px)
                
                    hist_data = hist_data_rect[:]
                    if args["showbackghisto"]:
                        hist_data.extend(hist_data_backg)

                # SHOW HISTOS
                if switch_new_ylim:
                    for hist_num in range(NUM_PLOTS):
                        
                        y_hist = np.histogram( hist_data[hist_num] )[0]
                        ymax = y_hist[1:].max()     #excluding bin0
                                    
                        livehist.set_ylim(y_lo = 0, y_hi = ymax * ylim_padding_mult
                                         ,ax_ind = (hist_num,) )
                        
                    switch_new_ylim = False

                livehist.update_figure( hist_data
                            ,ax_ind = range(NUM_PLOTS)
                            ,frames = 1
                            ,show = True
                            ,epsilon = .0001)
                
                last_hist_update = time.time()
 
        #SHOW IMAGES
        ret = showImages(img_display, b_show_main_img = True
                        ,b_show_transformed_img = True
                        ,img_t = img_t
                        ,b_show_mask_img = True
                        ,img_m = img_mask
                        )
        

        if cv2.waitKey(waitKeyRefresh)== ord('q'):
            print 'quitting'
            break
        
        if cv2.waitKey(waitKeyRefresh) == ord('o'):
    
            # options -----------------
            while(True):
                ret = raw_input('options ... show_histo, hide_histo, new_tracking_frame x0 y0 x1 y1, quit \n>')                

                if ret == 'quit':
                    break

                elif ret[:10] == "show_histo":
                    b_show_histos = True
                    b_histo = True
                
                elif ret[:10] == "hide_histo":
                    b_show_histos = False
                    b_histo = False

                elif ret[:18] == "new_tracking_frame":
                    
                    opt_args = ret.split(' ')
                    if len(opt_args) > 1:
                        try:
                            x0,y0,x1,y1 = int(opt_args[1]), int(opt_args[2]),  int(opt_args[3]), int(opt_args[4])
                            current_tracking_frame = ((x0,y0),(x1,y1))
                            print 'changing tracking_frame to: ', str(current_tracking_frame)
                            switch_new_ylim = True
                            print 'switching rect hist ylim'
                        except:
                            print 'could not set tracking_frame.'    
                    else:
                        print 'did not recognize length of tracking_frame input.'

                else:
                    print 'option <', str(ret),  '> not recognized'
            
            print 'quitting options...'
            # /options ----------------


        # DELAY FPS
        # if cam_type == 'file_cam':
        #     if b_slow_for_fps:
        #         current_frames_time = time.time() - time_last_frame 
        #         sleep_time = current_frames_time - fps_time - epsilon_fps_time
        #         if sleep_time > 0:
        #             time.sleep(sleep_time)
        #         time_last_frame = time.time()
        
        # LOGGING
        # if b_log:
        #     pass

        #Options -------------------------------------

    #Cleanup -------------------
    vc.release()
    cv2.destroyAllWindows()
    #if args['writebookvideo']: vw.release()

main()
print 'exiting main'