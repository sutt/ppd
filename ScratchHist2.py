import os,sys, random, copy
import cv2
import numpy as np

from modules.ImgUtils import px3clr_3px1clr as three_color
from modules.ImgUtils import px_to_list


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
    r_data = map(lambda f: round(f,round_places),data)
    if full:
        return str(r_data)
    short_data = [r_data[i] for i in range(len(r_data)) if i in short]
    return str(short_data)

def print_results2(data, full = False, round_places = 3, short = (1,2,3,4)):
    r_data = []
    for d in data:
        try:
            r_data.append( round(d,round_places) )
        except:
            r_data.append( d )
    if full:
        return str(r_data)
    short_data = [r_data[i] for i in range(len(r_data)) if i in short]
    return str(short_data)

def iter7(img, clrs = (0), goal_pct = 0.95, epsilon = 0.005, max_iter = 10, 
          log = False, steep = True):
    
    LO, HI = 0, 255

    clr_data = []
    c0,c1,c2 = cv2.split(img)
    clr_data.append(c0.flatten())
    clr_data.append(c1.flatten())
    clr_data.append(c2.flatten())
    
    #NEED to handle if not all clrs
    clr_range = []
    for c in clr_data:
        lo, hi = px_range(c) 
        clr_range.append( (lo,hi) )

    
    clr_lo = np.array( [cr[0] for cr in clr_range] )
    clr_hi = np.array( [cr[1] for cr in clr_range] )

    min_err = (1.0, 1.0, lo, hi, 0, -1)
    Log = []
    total = len(img)*len(img[0])

    if log:
        print 'INIT: ------------'
        print 'total pxs: %i' % total
        print 'color range: \n', "\n".join( map(lambda x: str(x), clr_range) )
        print 'clr_lo: ', str(clr_lo)
        print 'clr_hi: ', str(clr_hi)
    
    for i in range(0,max_iter):
        
        pct_i = pct_inrange_cv(img, clr_lo, clr_hi, total = total)
        
        p = 0
        for clr in clrs:
            lo, hi = clr_lo[clr], clr_hi[clr]
            p += (lo - LO) + (HI - hi)       
        if log: print 'p: ', str(p)
        
        err = abs( goal_pct - pct_i)    
        if err <= min_err[0]:
            min_err = (err, pct_i, clr_lo, clr_hi, p, i)

        if log: Log.append((err, pct_i, lo, hi, p, i))

        if (pct_i - epsilon) <= goal_pct <= (pct_i + epsilon):
            break

        if pct_i < goal_pct: 
            break

        if pct_i > goal_pct:
            
            gradient = []
            for clr_i in clrs:
                for side in ('lo', 'hi'):
                    if side == 'lo':
                        lo_delta = copy.copy(clr_lo)
                        lo_delta[clr_i] += 1
                        pir = pct_inrange_cv(img, lo_delta, clr_hi, total = total)
                    if side == 'hi':
                        hi_delta = copy.copy(clr_hi)
                        hi_delta[clr_i] -= 1
                        pir = pct_inrange_cv(img, clr_lo, hi_delta, total = total)
                    gradient.append(pct_i - pir)
            
            if log: print 'gradient: ', str(map(lambda f: round(f, 5), gradient)) 
            
            if steep:
                gradient_ind = max( enumerate(gradient), key = lambda tup: tup[1])[0]
            else:
                gradient_ind =  min( enumerate(gradient), key = lambda tup: tup[1])[0]

            f_clr = gradient_ind / 2
            f_side = 'lo' if (gradient_ind % 2 == 0) else 'hi'
            

            if f_side == 'lo':
                clr_lo[f_clr] += 1
            if f_side == 'hi':
                clr_hi[f_clr] -= 1

            if log: print clr_lo, clr_hi
            
    return min_err


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

    print '\nDEMO multi-color ----------------\n'
    out = iter7(img, clrs = (0,1,2), log = True, max_iter = 5, steep = True)
    print '3 color Decent: ', print_results2(out)

    print '\n Examples of 3-Color Descent -----------------\n'

    img = read_img(p = "data/write/july/imgs17/img1.jpg")

    #NOTE: p, penalty is computed wrong

    out = iter7(img, clrs = (0,1,2), goal_pct = 0.90, log = False, max_iter = 100, steep = True)
    print 'Steep 90pct: ', print_results2(out)
    out = iter7(img, clrs = (0,1,2), goal_pct = 0.90, log = False, max_iter = 100, steep = False)
    print 'Flat 90pct: ', print_results2(out)

    out = iter7(img, clrs = (0,1,2), goal_pct = 0.50, log = False, max_iter = 200, steep = True)
    print 'Steep 50pct: ', print_results2(out)
    out = iter7(img, clrs = (0,1,2), goal_pct = 0.50, log = False, max_iter = 200, steep = False)
    print 'Flat 50pct: ', print_results2(out)
