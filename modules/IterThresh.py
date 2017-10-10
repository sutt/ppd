import os,sys, random, copy
import cv2
import numpy as np

from ImgProcs import px_data, px_range, pct_inrange_cv


class F:
    
    def __init__(self, clrs = (0,1,2)):
        self.threshLo = [0,0,0]
        self.threshHi = [255,255,255]
        self.clrs = clrs
        self.p = 0

    def get_threshLo(self, **kwargs):
        if kwargs.get('np',False): 
            return np.array( self.threshLo, dtype = 'uint8' )
        return  self.threshLo
    def get_threshHi(self, **kwargs):
        if kwargs.get('np',False): 
            return np.array( self.threshHi, dtype = 'uint8' )
        return  self.threshHi
    
    def set_thresh(self, side, clr, val):
        if side == 'lo': self.threshLo[clr] = val
        if side == 'hi': self.threshHi[clr] = val

    def get_penalty(self, **kwargs):
        self.p = sum(self.threshLo) + sum(self.threshLo) - (255*3)
        return self.p
        
    def set_delta(self, side, clr, val = 1):
        if side == 'lo': self.threshLo[clr] += val
        if side == 'hi': self.threshHi[clr] -= val

class Gradient:
    
    def __init__(self, clrs = (0,1,2)):
        self.data = {}
        self.clrs = clrs
        self.data['lo'] = [0.0, 0.0, 0.0]
        self.data['hi'] = [0.0, 0.0, 0.0]

    def reset(self):
        self.data['lo'] = [0.0, 0.0, 0.0]
        self.data['hi'] = [0.0, 0.0, 0.0]

    def set(self, side, clr, val):
        self.data[side][clr] = val

    def get_best(self, steep = True):
        data = []
        data.extend(self.data['lo'])
        data.extend(self.data['hi'])
        data_t = [i_v for i_v in enumerate(data) if (i_v[0] / 2) in self.clrs]
        print 'clrs: ', str(self.clrs)
        if steep == True:
            ind = max( data_t, key = lambda tup: tup[1])[0]
        else:
            ind = min( data_t, key = lambda tup: tup[1])[0]

        g_clr = 2 - (ind % 3)
        g_side = 'lo' if (ind / 3 == 0) else 'hi'
        return (g_side,g_clr)
    

class ErrLog:
    
    def __init__(self):
        self.min_err = 1.0  #everything is less than 1.0
        self.misc = 1
    def update(self, err, misc):
        self.min_err = err
        self.misc = misc
    def get_min_err(self):
        return self.min_err
    def get_data(self):
        return (self.min_err,self.min_err)    
    
        
class Log:
    
    def __init__(self, b_log = False):
        self.b_log = b_log
        self.data = []
    
    def update(self, data):
        self.data = data
        
    def printout(self):
        print 'INIT: ------------'
        # print 'total pxs: %i' % total
        # print 'color range: \n', "\n".join( map(lambda x: str(x), clr_range) )
        # print 'clr_lo: ', str(clr_lo)
        # print 'clr_hi: ', str(clr_hi)
    


def iter7(img, clrs = (0,1,2), goal_pct = 0.95, steep = True
              ,epsilon = 0.005, max_iter = (255*3), b_log = False):
    
    CLRS = (0,1,2)

    clr_data = [c.flatten() for c in cv2.split(img)]
    clr_range = [px_range(c) for c in clr_data]

    f = F(clrs = clrs)
    for clr_i in CLRS:
        if clr_i in clrs:
            f.set_thresh(side = 'lo', clr = clr_i, val = clr_range[clr_i][0] )
            f.set_thresh(side = 'ho', clr = clr_i, val = clr_range[clr_i][1] )

    errLog = ErrLog()
    gradient = Gradient(clrs = clrs)
    log = Log(b_log)

    for _t in range(0,max_iter):
        
        print f.get_threshLo(np=True)
        print type(f.get_threshLo(np=True))
        pct_i = pct_inrange_cv(img, f.get_threshLo(np=True), f.get_threshHi(np=True))
        
        err = abs(goal_pct - pct_i)    
        if err <= errLog.get_min_err():
            misc = (_t, pct_i, err, f.get_threshLo(), f.get_threshHi(), f.get_penalty)
            errLog.update(err, misc)

        if (pct_i - epsilon) <= goal_pct <= (pct_i + epsilon):
            break

        if pct_i < goal_pct: 
            break

        if pct_i > goal_pct:
            
            gradient.reset()
            
            for clr_i in CLRS:
                if clr_i in clrs:
                    for side in ('lo', 'hi'):
                        
                        f_prime = copy.deepcopy(f)
                        f_prime.set_delta(side = side, clr = clr_i, val = 1)
                        
                        pir = pct_inrange_cv(img, f_prime.get_threshLo(np=True) 
                                                 ,f_prime.get_threshHi(np=True)
                                            )
                        
                        gradient.set(side = side, clr = clr_i, val = pct_i - pir)
            
            gradient_ind = gradient.get_best(steep = steep)
            
            f.set_delta(side = gradient_ind[0], clr = gradient_ind[1], val = 1)

            if log.b_log: log.update(_t)    #TODO, add all logging vars
                    
    return errLog



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

    out = iter7(img, clrs = (0,1,2), goal_pct = 0.90, b_log = False, max_iter = 100, steep = True)
    print 'Steep 90pct: ', print_results2(out)
    out = iter7(img, clrs = (0,1,2), goal_pct = 0.90, b_log = False, max_iter = 100, steep = False)
    print 'Flat 90pct: ', print_results2(out)

    out = iter7(img, clrs = (0,1,2), goal_pct = 0.50, b_log = False, max_iter = 200, steep = True)
    print 'Steep 50pct: ', print_results2(out)
    out = iter7(img, clrs = (0,1,2), goal_pct = 0.50, b_log = False, max_iter = 200, steep = False)
    print 'Flat 50pct: ', print_results2(out)

    out = iter7(img, clrs = (0,), goal_pct = 0.50, b_log = False, max_iter = 200, steep = True)
    print 'Color0 50pct: ', print_results2(out)
    out = iter7(img, clrs = (1,), goal_pct = 0.50, b_log = False, max_iter = 200, steep = True)
    print 'Color1 50pct: ', print_results2(out)
    out = iter7(img, clrs = (0,1), goal_pct = 0.50, b_log = False, max_iter = 200, steep = True)
    print 'Color1-2 Steep: ', print_results2(out)
    out = iter7(img, clrs = (0,1), goal_pct = 0.50, b_log = False, max_iter = 200, steep = False)
    print 'Color1-2 Flatt: ', print_results2(out)