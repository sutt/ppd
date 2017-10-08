import os,sys, random, copy
import cv2
import numpy as np


from ImgUtils import px3clr_3px1clr as three_color
from ImgUtils import px_to_list

#import os
#os.chdir('c:/users/wsutt/desktop/files/ppd/ppd/')
#import ScratchHist

def read_img(p = "data/write/july/imgs17/img1.jpg"):
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


def iter2(img, goal_pct = 0.95, epsilon = 0.005, max_iter = 10, log = False, steep = True):
    
    """ move either hi or lo"""

    t1 = px_to_list(img)
    t2 = three_color(t1)
    
    data = t2[2]
    lo, hi = 0, 255
    min_err = (1.0,1.0,0,255)
    
    for i in range(0,max_iter):
        
        pct_i = pct_inrange(data, lo_hi = (lo,hi))

        err = abs( goal_pct - pct_i)
        if err < min_err[0]:
            min_err = (err, pct_i, lo, hi)

        if log:
            print 'iter: %i' % i
            print 'pct_i: %f' % pct_i
            print 'lo: %i, hi: %i' % (lo, hi)

        if (pct_i - epsilon) <= goal_pct <= (pct_i + epsilon):
            break

        if pct_i < goal_pct: 
            break

        if pct_i > goal_pct:
            gradient_lo = pct_i - pct_inrange(data, lo_hi = (lo + 1,hi))
            gradient_hi = pct_i - pct_inrange(data, lo_hi = (lo,hi - 1))
            # take_low   (T)    (F)     NOT(XOR(L<W,STEEP))
            #           Steep  Flat
            # (T) L > W    T      F
            # (F) L < W    F      T
            take_lo = not( (gradient_lo > gradient_hi) != (steep) )
            f = (1,0) if take_lo  else (0,-1)
            lo, hi = lo + f[0], hi + f[1]    

        if lo < 0 : lo = 0
        if hi > 255: hi = 255
    
        #This doesnt work because 
        # (1000, 100, 100, ...) is a flatter gradient then (..., 500, 500, 500)
        # over a length of 3, but the first 1000 step will never be taken.

    return min_err

def px_data(img):
    return three_color(px_to_list(img))

def iter3(data, goal_pct = 0.95, epsilon = 0.005, max_iter = 10, log = False, steep = True):
    
    """ move either hi or lo"""
    LO, HI = 0, 255
    lo, hi = px_range(data) 
    #          err,pct_i,lo, hi, p, i      
    min_err = (1.0, 1.0, lo, hi, 0, -1)
    
    for i in range(0,max_iter):
        
        pct_i = pct_inrange(data, lo_hi = (lo,hi))
        
        p = (lo - LO) + (HI - hi)       #penalty
        
        err = abs( goal_pct - pct_i)    #best iter
        if err <= min_err[0]:
            min_err = (err, pct_i, lo, hi, p, i)

        if log:
            print 'iter: %i' % i
            print 'pct_i: %f' % pct_i
            print 'lo: %i, hi: %i' % (lo, hi)

        if (pct_i - epsilon) <= goal_pct <= (pct_i + epsilon):
            break

        if pct_i < goal_pct: 
            break

        if pct_i > goal_pct:
            gradient_lo = pct_i - pct_inrange(data, lo_hi = (lo + 1,hi))
            gradient_hi = pct_i - pct_inrange(data, lo_hi = (lo,hi - 1))
            # take_low   (T)    (F)     NOT(XOR(L<H,STEEP))
            #           Steep  Flat
            # (T) L > H    T      F
            # (F) L < H    F      T
            take_lo = not( (gradient_lo > gradient_hi) != (steep) )
            f = (1,0) if take_lo  else (0,-1)
            lo, hi = lo + f[0], hi + f[1]    
            
    return min_err


def iter4(data, goal_pct = 0.95, epsilon = 0.005, max_iter = 10, 
          log = False, steep = True, init_n = 20):
    
    """ move either hi or lo"""
    LO, HI = 0, 255
    lo, hi = px_range(data) 
    
    n = init_n
    
    #          err,pct_i,lo, hi, p, i      
    min_err = (1.0, 1.0, lo, hi, 0, -1)
    Log = []
    
    for i in range(0,max_iter):
        
        pct_i = pct_inrange(data, lo_hi = (lo,hi))
        
        p = (lo - LO) + (HI - hi)       #penalty
        
        err = abs( goal_pct - pct_i)    #best iter
        if err <= min_err[0]:
            min_err = (err, pct_i, lo, hi, p, i)

        if log: Log.append((err, pct_i, lo, hi, p, i))

        if (pct_i - epsilon) <= goal_pct <= (pct_i + epsilon):
            break

        if pct_i < goal_pct: 
            break

        #first check for lo or hi to not be great enough


        if pct_i > goal_pct:
            gradient_lo = pct_i - pct_inrange(data, lo_hi = (lo + 1,hi))
            gradient_hi = pct_i - pct_inrange(data, lo_hi = (lo,hi - 1))
            # take_low   (T)    (F)     NOT(XOR(L<H,STEEP))
            #           Steep  Flat
            # (T) L > H    T      F
            # (F) L < H    F      T
            take_lo = not( (gradient_lo > gradient_hi) != (steep) )
            f = (1,0) if take_lo  else (0,-1)
            lo, hi = lo + f[0], hi + f[1]    
            
    return min_err
            
def iter5(data, lo, hi, pct_0, epsilon = 0.005, 
          log = False, steep = True, init_n = 10):
    
    """ move either hi or lo"""
    
    LO, HI = 0, 255
    lo, hi = lo, hi
    p = (lo - LO) + (HI - hi)      

    n = min(init_n, p)
    b_solved = False

    #          err,pct_i,lo, hi, p, i, j      
    min_err = (1.0, 1.0, lo, hi, p, -1)
    Log = []
    
    for j in (-1,1):
        for i in range(1,n+1):
                
                lo, hi = lo + i*j, hi - i*j

                pct_i = pct_inrange(data, lo_hi = (lo,hi))
                
                if pct_i < pct_0:
                    min_err = (err, pct_i, lo, hi, p, i)
                    b_solved = True

                if log: Log.append((err, pct_i, lo, hi, p, i))

                if b_solved: return min_err
            
    return min_err

def scratch1(img):
    LO, HI = 0, 255
    lo, hi = 30, 255
    mask = cv2.inRange(img, (lo, LO, LO), (hi,HI, HI))
    return mask

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
    
    total = len(img)*len(img[0])
    print 'total: ', str(total)

             # err,pct_i,lo, hi, p, i      
    min_err = (1.0, 1.0, lo, hi, 0, -1)
    Log = []
    
    for i in range(0,max_iter):
        
        pct_i = pct_inrange_cv(img,tup_lo,tup_hi, total = total)
        
        p = (lo - LO) + (HI - hi)       #penalty
        
        err = abs( goal_pct - pct_i)    #best iter
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



if __name__ == "__main__":
    
    #os.chdir("ppd/")
    img = read_img(p = "data/write/july/imgs17/rect1.jpg")
    #img = read_img(p = "data/write/july/imgs17/img1.jpg")
    #mask = scratch1(img)
    #print np.sum(mask) / 255
    #print np.sum(img) 
    #print len(img)*len(img[0])
    #print mask[:10]

    out = iter6(img,clr=0, max_iter =200)
    print out

    #t2 = main()
    #print px_range(t2[0])
    #print pct_inrange(t2[0], lo_hi = (0,255))
    #print pct_inrange(t2[0], lo = 100)
    #print pct_inrange(t2[0], lo_hi = (50,200))

    # img = read_img()
    # output = iter1(img, log=True)

    # img = read_img()
    # output = iter2(img, goal_pct = 0.95, max_iter = 4, log=True)
    # print 'SOLVED: ', str(output)

    # output = iter2(img, goal_pct = 0.95, max_iter = 4, log=True, steep = False)
    # print 'SOLVED: ', str(output)

    # img2 = read_img(p = "data/write/july/imgs17/rect1.jpg")
    # d = px_data(img2)
    
    # output = iter3(d[1], goal_pct = 0.95, max_iter = 100, log=False)
    # print 'SOLVED: ', str(output)
    # output = iter3(d[1], goal_pct = 0.95, max_iter = 100, log=False, steep = False)
    # print 'SOLVED: ', str(output)

    # output = iter3(d[2], goal_pct = 0.95, max_iter = 100, log=False)
    # print 'SOLVED: ', str(output)
    # output = iter3(d[2], goal_pct = 0.95, max_iter = 100, log=False, steep = False)
    # print 'SOLVED: ', str(output)

    # img2 = read_img(p = "data/write/july/imgs17/rect1.jpg")
    # #img2 = read_img(p = "data/write/july/imgs17/img1.jpg")
    # d = px_data(img2)
    
    # output = iter3(d[0], goal_pct = 0.95, max_iter = 100, log=False)
    # print 'SOLVED: ', str(output)
    # output = iter3(d[0], goal_pct = 0.95, max_iter = 100, log=False, steep = False)
    # print 'SOLVED: ', str(output)
    # _err, _pct, _lo, _hi, _p, _i = output
    # print iter5(d[0],_lo,_hi,_pct)

    # output = iter3(d[1], goal_pct = 0.95, max_iter = 100, log=False)
    # print 'SOLVED: ', str(output)
    # output = iter3(d[1], goal_pct = 0.95, max_iter = 100, log=False, steep = False)
    # print 'SOLVED: ', str(output)
    # _err, _pct, _lo, _hi, _p, _i = output
    # print iter5(d[1],_lo,_hi,_pct)

    # output = iter3(d[2], goal_pct = 0.95, max_iter = 100, log=False)
    # print 'SOLVED: ', str(output)
    # output = iter3(d[2], goal_pct = 0.95, max_iter = 100, log=False, steep = False)
    # print 'SOLVED: ', str(output)
    # _err, _pct, _lo, _hi, _p, _i = output
    # print iter5(d[2],_lo,_hi,_pct)

    # output = iter3(d[1], goal_pct = 0.95, max_iter = 15, log=True)
    # print 'SOLVED: ', str(output)
    # output = iter3(d[1], goal_pct = 0.95, max_iter = 15, log=True, steep = False)
    # print 'SOLVED: ', str(output)

    
