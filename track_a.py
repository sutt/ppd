import numpy as np
import cv2
import imutils
from collections import deque
from matplotlib import image as mpimg

from matplotlib import pyplot as plt


def multi_plot(inp_imgs):
    for img in inp_imgs:
        plt.imshow(img)
        plt.show()

def transform1(frame):
    
    greenLower = (25,25,25)
    greenUpper = (45,45,45)
    pts = deque(maxlen=64)

    #frame = imutils.resize(frame, width=600)
    blurred = cv2.GaussianBlur(frame, (11, 11), 0)
    #hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv = blurred
    
    mask = cv2.inRange(hsv, greenLower, greenUpper)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)
    
    return mask

def find_xy(mask):

    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE)[-2]

    if len(cnts) > 0:
        c = max(cnts, key=cv2.contourArea)
        ((x, y), radius) = cv2.minEnclosingCircle(c)
        
    return (x,y)

def find_radius(mask):

    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE)[-2]

    if len(cnts) > 0:
        c = max(cnts, key=cv2.contourArea)
        ((x, y), radius) = cv2.minEnclosingCircle(c)
        
        
    return radius

def filter_success(min_radius = 10):
        return radius >= min_radius
            
def draw_tracking1(x,y,radius,frame):
            
    cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
    #cv2.circle(frame, center, 5, (0, 0, 255), -1)

    return frame


def track(pic):
    """ ((x,y),radius)  """
    tframe = transform1(pic)
    center = find_xy(tframe)
    radius = find_radius(tframe)
    return center,radius



def batch_files(read_path):    
    
    read_path = 'C:\\Users\\wsutt\\Desktop\\files\\ppd\\ppd'
    #read_path = os.getcwd()
    files = os.listdir(read_path)

    picfn = []
    for f in files:
        if 'pic' in f:
            picfn.append(f)
    print picfn

    fn_nums = map(lambda chars: int( chars.split('pic')[1].split('.')[0] ), picfn )
    fn_nums.sort()
    ordered_picfn = map( lambda c: "pic"+str(c)+".jpg", fn_nums)

    imgs = []
    for fn_i in ordered_picfn:
        imgs.append( cv2.imread(readpath + '\\' + fn_i))

    return imgs
        
    
def batch_track(imgs):    

    track_params = []
    for _img in imgs:
        track_params.append(track(_img))
    return track_params
        
def batch_timeit(imgs):

    import time
    times = []
    for _img in imgs:
        t0 = time.time()
        dummy = track(_img)
        t = time.time() - t0
        times.append(t)
    return times

def batch(read_path):
    imgs = batch_files(read_path)    
    print 'reading '
    tracked = batch_track(imgs)
    print 'num tracked imgs: ', len(tracked)
    timed = batch_timeit(imgs)
    print 'avg time: ', float(sum(timed)) / float(len(time))
    print 'min time: ', time.min()
    print 'max time: ', time.max()
    return tracked



    


def flat_3clr(pic):
    return [ tuple([pic[h,w,clr] for clr in range(3)]) for h in range(pic.shape[0]) for w in range(pic.shape[1]) ]
      
bgr_my_img = flat_3clr(my_img)

color_histo = []
for i in range(3):
    color_histo.append(bgr_my_img[i])
    
plt.hist(color_histo[0], bins = 255, range = (0,255))
plt.show()
plt.hist(color_histo[1], bins = 255, range = (0,255))
plt.show()