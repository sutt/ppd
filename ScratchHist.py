import cv2
import numpy as np
import os,sys, random

from ImgUtils import px3clr_3px1clr as three_color
from ImgUtils import px_to_list

#import os
#os.chdir('c:/users/wsutt/desktop/files/ppd/ppd/')
#import ScratchHist

def read_img():
    p = "data/write/july/imgs17/img1.jpg"
    img = cv2.imread(p)
    return img

def main():
    
    p = "data/write/july/imgs17/img1.jpg"
    img = cv2.imread(p)

    print 'len of img: %i' % len(img)

    t1 = px_to_list(img)
    t2 = three_color(t1)

    print 'len of t1: %i' % len(t1)
    print 'len of t2: %i' % len(t2)
    print 'len of t2[0]: %i' % len(t2[0])

    return t2

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

def iter1(img, goal_pct = 0.95, epsilon = 0.005, max_iter = 10, log = False):

    t1 = px_to_list(img)
    t2 = three_color(t1)
    
    data = t2[1]
    lo, hi = 0, 255
    direction = 0
    
    for i in range(0,max_iter):
        
        pct_i = pct_inrange(data, lo_hi = (lo,hi))

        if log:
            print 'iter: %i' % i
            print 'pct_i: %f' % pct_i
            print 'lo: %i, hi: %i' % (lo, hi)

        if (pct_i - epsilon) <= goal_pct <= (pct_i + epsilon):
            if log:
                print 'solved, iter: %i' % i
            break

        if pct_i > goal_pct:
            if direction == -1:
                lo += 1
                hi -= 1
                direction = -1
            else:
                rand = random.sample([-1,1],1)[0]
                if rand == -1:
                    lo += 1
                else:
                    hi -= 1
                direction = 0
                
            
        if pct_i < goal_pct:
            if direction == 0:
                if rand == -1:
                    lo -= 1
                else:
                    hi += 1
            else:
                lo -= 1
                hi += 1
                direction = 1
            
        if lo < 0 : lo = 0
        if hi > 255: hi = 255
    
    return (pct_i, lo, hi)


def iter2(img, goal_pct = 0.95, epsilon = 0.005, max_iter = 10, log = False):
    
    """ move either hi or lo"""

    t1 = px_to_list(img)
    t2 = three_color(t1)
    
    data = t2[1]
    lo, hi = 0, 255
    min_err = (1.0,1.0,0,255)
    
    for i in range(0,max_iter):
        
        pct_i = pct_inrange(data, lo_hi = (lo,hi))

        if log:
            print 'iter: %i' % i
            print 'pct_i: %f' % pct_i
            print 'lo: %i, hi: %i' % (lo, hi)

        if (pct_i - epsilon) <= goal_pct <= (pct_i + epsilon):
            break

        err = abs( goal_pct - pct_i)
        if err < min_err[0]:
            min_err = (err, pct_i, lo, hi)

        if pct_i < goal_pct: break

        if pct_i > goal_pct:
            gradient_lo = pct_inrange(data, lo_hi = (lo + 1,hi))
            gradient_hi = pct_inrange(data, lo_hi = (lo,hi - 1))
            if log: print 'g_lo: %f, g_hi: % f' % (gradient_lo,gradient_hi)
            f = (1,0) if gradient_lo > gradient_hi else (0,-1)
            lo, hi = lo + f[0], hi + f[1]    

        if lo < 0 : lo = 0
        if hi > 255: hi = 255
    
        #This doesnt work because 
        # (1000, 100, 100, ...) is a flatter gradient then (..., 500, 500, 500)
        # over a length of 3, but the first 1000 step will never be taken

    return (pct_i, lo, hi)
            



if __name__ == "__main__":
    t2 = main()
    print px_range(t2[0])
    print pct_inrange(t2[0], lo_hi = (0,255))
    print pct_inrange(t2[0], lo = 100)
    print pct_inrange(t2[0], lo_hi = (50,200))

    # img = read_img()
    # output = iter1(img, log=True)

    img = read_img()
    output = iter2(img, goal_pct = 0.95, log=True)

    print 'SOLVED: ', str(output)

