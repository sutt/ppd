import os, sys, time, copy, random
import traceback
import numpy as np
import cv2
import imutils
from collections import deque
from matplotlib import image as mpimg
from matplotlib import pyplot as plt

from track_a import find_xy, find_radius
from GraphicsA import LiveHist

#hello()

def px3clr_3px1clr(list_pixels):
    return [ map( lambda v: v[clr], list_pixels ) for clr in range(3)]

def px_to_list(img):
    hL,wL = img.shape[0], img.shape[1]  
    return [ tuple( img[h,w,:] ) for h in range(hL) for w in range(wL) ]
            
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
        
def showImages(img_display,**kwargs):
    
    if not(kwargs.get('dont_mirror',False)):
        img_display = cv2.flip(img_display,1)

    if kwargs.get('b_show_main_img', False):
        cv2.imshow('display image', img_display)
        #plt.imshow(img_display, cvtColor)
    
    if kwargs.get('b_show_transformed_img', False):
        cv2.imshow('transformed image', kwargs.get('img_p',None) )

    if kwargs.get('b_show_tracked_img', False):
        cv2.imshow('the ball',kwargs.get('on_pxs',None))

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

def main():

    #Init and Params ---------------------------
    cam_params = (640,480)
    h_img, w_img = cam_params[0], cam_params[1]
    waitKeyRefresh = 1
    cam_type = 'cv_cam'     # 'pi_cam' 'file_cam'
    
    current_tracking_frame = ((100,100),(300,300))
    b_tracking_frame = True
    b_tracking_frame_2 = False
    b_histo = True
    b_hist_rect = True
    b_show_histos = True

    b_drawTracking = True

    time_last = time.time()

    info_annotations = []

    
    vc = initCam(cam_type)
    vc = setupCam(vc, cam_type = cam_type, params = cam_params)

    if b_show_histos:
        lh = LiveHist(h=1,w=3, bins = 30, x_lo = -1, x_hi = 256)
        NUM_COLORS = 3  
        lh.show_plt(wait_time = 1)
        last_hist_update = time.time()
        hist_update_hz = 1      #.3 is on the borderline of usable


    while(vc.isOpened()):

        
        ret, frame = getFrame(vc, cam_type = 'cv_cam')        
        if not(ret): break

        if b_tracking_frame_2:
            current_tracking_frame = create_tracking_frame()
            img = crop_img(frame, current_tracking_frame)
        else:
            img = frame[:,:,:]

        # THRESHOLD MASK
        img_p = transformA(img, b_hsv = True)
        Lo, Hi = (29, 86, 6), (64, 255, 255)
        mask = threshA(img_p, threshLo = Lo , threshHi = Hi )
        mask = repairA(mask, iterations = 2)
        

        # LOCATE / TRACK
        x,y = find_xy(mask)
        radius = find_radius(mask)
        #print x, ' ', y, ' ', radius
        
        # if b_tracking_frame:
        #     x,y,radius = decrop_track(h_img, w_img)
        # b_track_success = filter_track()
        b_track_success = True

        # HISTO_PROCESSING
        if b_histo:
            rect_img = crop_img(frame.copy(), current_tracking_frame)
            rect_histos = hist_from_img(rect_img)
            
            if len(rect_histos) == 3:
                for h in rect_histos:
                    print h[:min(5,len(h))]
            else:
                print rect_histos
            #data
            #ball_vs_background()
        

        #DRAW ONTO FRAME
        img_display = frame

        b_tracking_frame = True
        if b_tracking_frame:
            img_display = draw_tracking_frame(frame,x,y,radius)

        if b_drawTracking: # and b_track_success:
            img_display = draw_tracking(img_display,current_tracking_frame)

        b_annotate_img = False
        if b_annotate_img:
            img_display = draw_annotations(img_display, info_annotations)       
            

        # SHOW HISTOS
        if b_show_histos:
            
            if time.time() - last_hist_update > hist_update_hz:
                u, var = rand_gauss_params()
                data = map( lambda x: mock_gaussian(n=100,u=u,var=var), range(NUM_COLORS) )
                lh.update_figure( data
                            ,ax_ind = range(NUM_COLORS)
                            ,frames = 1
                            ,show = True
                            ,epsilon = .0001)
                last_hist_update = time.time()
 
        #SHOW IMAGES
        ret = showImages(img_display, b_show_main_img = True
                        ,b_show_transformed_img = True
                        ,img_p = mask)
        

        if cv2.waitKey(waitKeyRefresh)== ord('q'):
            print 'quitting'
            break
        
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