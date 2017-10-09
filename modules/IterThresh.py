import os,sys, random, copy
import cv2
import numpy as np

from ImgProcs import px_data, px_range, pct_inrange_cv

def iter7(img, clrs = (0), goal_pct = 0.95, epsilon = 0.005, max_iter = 10, 
          log = False, steep = True):
    
    
    CLRS = (0,1,2)
    LO, HI = 0, 255

    clr_data = [c.flatten() for c in cv2.split(img)]
    
    clr_range = [px_range(c) for c in clr_data]

    clr_lo = np.array( [cr[0] for cr in clr_range] )
    clr_hi = np.array( [cr[1] for cr in clr_range] )

    min_err = (1.0, 1.0, 0, 255, 0, -1)
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
            for clr_i in CLRS:
                if not(clr_i in clrs):
                    gradient.append(-2.0)
                    gradient.append(-2.0)
                else:
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
                gradient_ind = max( enumerate(gradient), 
                                    key = lambda tup: tup[1] if tup[1] != -2.0 else -2.0)[0]
            else:
                gradient_ind =  min( enumerate(gradient), 
                                    key = lambda tup: tup[1] if tup[1] != -2.0 else 2.0)[0]

            f_clr = gradient_ind / 2
            f_side = 'lo' if (gradient_ind % 2 == 0) else 'hi'
            

            if f_side == 'lo':
                clr_lo[f_clr] += 1
            if f_side == 'hi':
                clr_hi[f_clr] -= 1

            if log: print clr_lo, clr_hi
            
    return min_err

if __name__ == "__main__":

    p = "../data/write/july/imgs17/img1.jpg"
    img = cv2.imread(p)

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

    out = iter7(img, clrs = (0,1,2), goal_pct = 0.90, log = False, max_iter = 100, steep = True)
    print 'Steep 90pct: ', print_results2(out)
    out = iter7(img, clrs = (0,1,2), goal_pct = 0.90, log = False, max_iter = 100, steep = False)
    print 'Flat 90pct: ', print_results2(out)

    out = iter7(img, clrs = (0,1,2), goal_pct = 0.50, log = False, max_iter = 200, steep = True)
    print 'Steep 50pct: ', print_results2(out)
    out = iter7(img, clrs = (0,1,2), goal_pct = 0.50, log = False, max_iter = 200, steep = False)
    print 'Flat 50pct: ', print_results2(out)

    out = iter7(img, clrs = (0,), goal_pct = 0.50, log = False, max_iter = 200, steep = True)
    print 'Color0 50pct: ', print_results2(out)
    out = iter7(img, clrs = (1,), goal_pct = 0.50, log = False, max_iter = 200, steep = True)
    print 'Color1 50pct: ', print_results2(out)
    out = iter7(img, clrs = (0,1), goal_pct = 0.50, log = False, max_iter = 200, steep = True)
    print 'Color1-2 Steep: ', print_results2(out)
    out = iter7(img, clrs = (0,1), goal_pct = 0.50, log = False, max_iter = 200, steep = False)
    print 'Color1-2 Flatt: ', print_results2(out)