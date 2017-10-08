import os,sys, random, copy
import cv2
import numpy as np

from ImgUtils import px3clr_3px1clr as three_color
from ImgUtils import px_to_list


def read_img(p = "data/write/july/imgs17/img1.jpg"):
    img = cv2.imread(p)
    return img

def px_data(img):
    return three_color(px_to_list(img))

def px_range(data):
    return min(data), max(data)

def pct_inrange(data, lo_hi = (0,255), **kwargs):
    
    """returns [0,1] float for how many px's are in range"""

    if len(lo_hi) != 2:
        return -1

    if kwargs.get('lo',-1) > -1: lo_hi = (kwargs.get('lo',-1), lo_hi[1] )
    if kwargs.get('hi',-1) > -1: lo_hi[1] = (lo_hi[0], kwargs.get('hi',-1) )

    total_pxs = len(data)
    lo,hi = lo_hi[0], lo_hi[1]
    inrange = filter(lambda v: lo <= v <= hi, data)

    total_in = len(inrange)

    return float(total_in) / float(total_pxs)


def pct_inrange_cv(img, lo, hi, total = 0):
    t_mask = cv2.inRange(img, lo, hi )
    t_i = np.sum( t_mask  ) / 255
    if total == 0: total = len(img)*len(img[0])
    pct_i = float(t_i) / float(total)
    return pct_i


def iter6(img, clr = 0, goal_pct = 0.95, epsilon = 0.005, max_iter = 10, 
          log = False, steep = True):
    
    LO, HI = 0, 255
    img2 = img.copy()
    data = px_data(img2)[clr]
    lo, hi = px_range(data) 
    
    tup_lo = np.array([LO if clr != j else lo for j in range(3)])
    tup_hi = np.array([HI if clr != j else hi for j in range(3)])

    min_err = (1.0, 1.0, lo, hi, 0, -1)
    Log = []
    total = len(img)*len(img[0])
    
    for i in range(0,max_iter):
        
        pct_i = pct_inrange_cv(img,tup_lo,tup_hi, total = total)
        
        p = (lo - LO) + (HI - hi)       
        
        err = abs( goal_pct - pct_i)    
        if err <= min_err[0]:
            min_err = (err, pct_i, lo, hi, p, i)

        if log: Log.append((err, pct_i, lo, hi, p, i))

        if (pct_i - epsilon) <= goal_pct <= (pct_i + epsilon):
            break

        if pct_i < goal_pct: 
            break

        if pct_i > goal_pct:
            
            temp_tup_lo = np.array([LO if clr != i else lo + 1 for i in range(3)])
            temp_tup_hi = np.array([HI if clr != i else hi - 1 for i in range(3)])
            gradient_lo = pct_i - pct_inrange_cv(img,temp_tup_lo,tup_hi, total = total)
            gradient_hi = pct_i - pct_inrange_cv(img,tup_lo,temp_tup_hi, total = total)
            if log: print 'grad_lo: %f | grad_hi: %f' % (gradient_lo,gradient_hi)
            
            # take_lo    (T)    (F)     NOT(XOR(L<H,STEEP))
            #           Steep  Flat
            # (T) L > H    T      F
            # (F) L < H    F      T
            take_lo = not( (gradient_lo > gradient_hi) != (steep) )
            f = (1,0) if take_lo  else (0,-1)
            lo, hi = lo + f[0], hi + f[1]    
            tup_lo = np.array([LO if clr != j else lo for j in range(3)])
            tup_hi = np.array([HI if clr != j else hi for j in range(3)])
            if log: print tup_lo, tup_hi
            
    return min_err

def print_results(data, full = False, round_places = 3, short = (1,2,3,4)):
    r_data = map(lambda f: round(f,round_places),out)
    if full:
        return str(r_data)
    short_data = [r_data[i] for i in range(len(r_data)) if i in short]
    return str(short_data)

if __name__ == "__main__":

    img = read_img(p = "data/write/july/imgs17/rect1.jpg")

    print 'DEMO: ----------------------'
    out = iter6(img, clr = 0, log = True, max_iter = 5, steep = True)
    print 'end demo ------------------- \n'

    clr = 0
    out = iter6(img, clr = clr, log = False, max_iter = 200, steep = True)
    print 'Steep Decent: ', print_results(out)
    out = iter6(img, clr = clr, log = False, max_iter = 200, steep = False)
    print 'Flatt Decent: ', print_results(out)

    clr = 1
    out = iter6(img, clr = clr, log = False, max_iter = 200, steep = True)
    print 'Steep Decent: ', print_results(out)
    out = iter6(img, clr = clr, log = False, max_iter = 200, steep = False)
    print 'Flatt Decent: ', print_results(out)

    clr = 2
    out = iter6(img, clr = clr, log = False, max_iter = 200, steep = True)
    print 'Steep Decent: ', print_results(out)
    out = iter6(img, clr = clr, log = False, max_iter = 200, steep = False)
    print 'Flatt Decent: ', print_results(out)


