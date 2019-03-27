import os,sys, random, copy
import cv2
import numpy as np
from imgprocs import (px_range, pct_inrange_cv)
from shapesmisc import shapes_seen

'''
    gradient descent methods iterThreshA, iterThreshB 

    methods are not useful in practive see: books/iterThreshA-vizdebug.ipynb
'''

class F:
    
    def __init__(self, clrs = (0,1,2)):
        self.threshLo = [0,0,0]
        self.threshHi = [255,255,255]
        self.clrs = clrs
        self.p = 0
        self.x_end = [True] * 6

    def get_threshLo(self, **kwargs):
        if kwargs.get('np',False): 
            return np.array( self.threshLo, dtype = 'uint8' )
        return  copy.copy(self.threshLo)

    def get_threshHi(self, **kwargs):
        if kwargs.get('np',False): 
            return np.array( self.threshHi, dtype = 'uint8' )
        return  copy.copy(self.threshHi)
    
    def set_thresh(self, side, clr, val):
        if side == 'lo': self.threshLo[clr] = val
        if side == 'hi': self.threshHi[clr] = val

    def get_penalty(self, **kwargs):
        self.p = sum(self.threshLo) - sum(self.threshHi) + (255*3)
        return self.p
        
    def get_x_end(self):
        return copy.copy(self.x_end)

    def set_delta_widen(self, side, clr, val = 1):
        if side == 'lo': 
            if self.threshLo[clr] > 0:
                self.threshLo[clr] -= val
        if side == 'hi': 
            if self.threshHi[clr] < 255:
                self.threshHi[clr] += val

    def set_delta(self, side, clr, val = 1):
        if side == 'lo': 
            if self.threshLo[clr] == 0:
                self.x_end[0 + clr] = False
            if self.x_end[0 + clr]:
                self.threshLo[clr] += val
        if side == 'hi': 
            if self.threshHi[clr] == 255:
                self.x_end[3 + clr] = False
            if self.x_end[3 + clr]:
                self.threshHi[clr] -= val
            

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

    def get_data(self):
        data = []
        data.extend(self.data['lo'])
        data.extend(self.data['hi'])
        return data

    def get_best(self, steep = True, x_end = [True]*6, randomize = False):
        data = []
        data.extend(self.data['lo'])
        data.extend(self.data['hi'])
        data_t = [i_v for i_v in enumerate(data) ]
        data_t = [data_t[i] for i in range(6) if x_end[i] ]
        data_t = filter( lambda i_v: (i_v[0] % 3) in self.clrs, data_t)

        if steep == True:
            _max_iv = max( data_t, key = lambda tup: tup[1])
            ind = _max_iv[0]
        else:
            _min_iv = min( data_t, key = lambda tup: tup[1])
            ind = _min_iv[0]
        
        if randomize:
            if steep == True:
                _max_inds = filter(lambda i_v: i_v[1] == _max_iv[1], data_t )
                if len(_max_inds) > 1:
                    ind = random.sample(_max_inds,1)[0][0]
            else:
                _min_inds = filter(lambda i_v: i_v[1] == _min_iv[1], data_t )
                if len(_min_inds) > 1:
                    ind = random.sample(_min_inds,1)[0][0]


        g_clr = ind % 3
        g_side = 'lo' if (ind / 3 == 0) else 'hi'
        return (g_side,g_clr)

    def get_best_random(self, steep = True):
        g_side = str(['lo','hi'][int(random.uniform(0,1))])
        g_clr = int(random.uniform(0,2))
        return (g_side,g_clr)
    
    

class ErrLog:
    
    def __init__(self, **kwargs):
        self.min_err = float(kwargs.get('init_err',1.0))  #everything is less than 1.0
        self.max_rad = 0
        self.total_contours = 0
        self.misc = 1
        self.log = None
    def update(self, err, misc):
        self.min_err = err
        self.misc = misc
    def add_log(self, log):
        self.log = log
    def get_min_err(self):
        return self.min_err
    def get_data(self):
        return (self.min_err,self.misc,self.log)    
    
        
class Log:
    
    def __init__(self, b_log = False):
        self.b_log = b_log
        self.data = []
    
    def update(self, data):
        self.data.append( data )

    def get_data(self):
        return copy.deepcopy(self.data)
        

def combine_threshes(data, liberal = True ):
    if len(data) < 1:
        print 'not any data in log'
        return (  np.array( [0,0,0], dtype = 'uint8' ),
                  np.array( [255,255,255], dtype = 'uint8' ) )
    else:
        _lo, _hi = [[255,255,255], [0,0,0]]
        for row in data:
            lo, hi = row[0], row[1]
            for i,clr in enumerate(lo):
                if clr < _lo[i]: _lo[i] = clr
            for i,clr in enumerate(hi):
                if clr > _hi[i]: _hi[i] = clr
    return ( np.array( _lo, dtype = 'uint8') 
            ,np.array( _hi, dtype = 'uint8') )



def iterThreshA(img, clrs = (0,1,2), goal_pct = 0.95, steep = True
              ,epsilon = 0.005, max_iter = (255*3), b_log = False):
    
    CLRS = (0,1,2)

    clr_data = [c.flatten() for c in cv2.split(img)]
    clr_range = [px_range(c) for c in clr_data]

    f = F(clrs = clrs)
    for clr_i in CLRS:
        if clr_i in clrs:
            f.set_thresh(side = 'lo', clr = clr_i, val = clr_range[clr_i][0] )
            f.set_thresh(side = 'hi', clr = clr_i, val = clr_range[clr_i][1] )

    errLog = ErrLog()
    gradient = Gradient(clrs = clrs)
    log = Log(b_log)

    for _t in range(0,max_iter):
        
        pct_i = pct_inrange_cv(img, f.get_threshLo(np=True), f.get_threshHi(np=True))
        
        err = abs(goal_pct - pct_i)    
        if err <= errLog.get_min_err():
            misc = (_t, pct_i, err, f.get_threshLo(), f.get_threshHi(), f.get_penalty())
            errLog.update(err, misc)

        if (pct_i - epsilon) <= goal_pct <= (pct_i + epsilon):
            break

        if pct_i < goal_pct: 
            break
            # f.reset_last_change()
            # b_dont_go_lower = True
            # continue

        if pct_i > goal_pct:
            
            gradient.reset()
            
            for clr_i in CLRS:
                if clr_i in clrs:
                    for side in ('lo', 'hi'):
                        
                        f_prime = copy.deepcopy(f)
                        f_prime.set_delta(side = side, clr = clr_i, val = 1)
                        
                        pct_prime = pct_inrange_cv(img, f_prime.get_threshLo(np=True) 
                                                       ,f_prime.get_threshHi(np=True) )
                                            
                        gradient.set(side = side, clr = clr_i, val = pct_i - pct_prime)
            
            gradient_ind = gradient.get_best(steep = steep)
            
            if log.b_log: 
                log.update( (_t, pct_i, err, f.get_threshLo(), f.get_threshHi()
                            ,gradient.get_data(), gradient_ind, f.get_penalty() 
                           ) ) 

            f.set_delta(side = gradient_ind[0], clr = gradient_ind[1], val = 1)
                    
    if log.b_log: errLog.add_log(log.get_data())
    return errLog.get_data()

def tracked_shapes(img, thresh, b_max_radius = True):
    
    s = shapes_seen(img, thresh, blur = 11, repair_iters = 0, b_ret_radius = True, b_ret_area = False)

    if len(s) == 0:
        return 0
    if b_max_radius:
        max_s = max(s)
        return max_s
    return 0


def iterThreshB(img, init_thresh = ((126,126,126),(127,127,127)) , clrs = (0,1,2), 
                e_goal = 10.0, steep = True, epsilon = 1.0, 
                max_iter = (255*3), b_log = False, **kwargs):
    
    """ this one uses a penalty as a function of background-img and amount of contours
    that are found in the background image"""
    
    CLRS = (0,1,2)

    clr_data = [c.flatten() for c in cv2.split(img)]
    clr_range = [px_range(c) for c in clr_data]

    f = F(clrs = clrs)
    for clr_i in CLRS:
        if clr_i in clrs:
            f.set_thresh(side = 'lo', clr = clr_i, val = init_thresh[0][clr_i] )
            f.set_thresh(side = 'hi', clr = clr_i, val = init_thresh[1][clr_i] )

    errLog = ErrLog(init_err = e_goal)
    gradient = Gradient(clrs = clrs)
    log = Log(b_log)

    for _t in range(0,max_iter):
        
        e_i = tracked_shapes(img, (f.get_threshLo(np=True), f.get_threshHi(np=True)))
        
        err = abs(e_goal - e_i)    
        #if err < errLog.get_min_err():
        misc = (_t, e_i, err, f.get_threshLo(), f.get_threshHi(), f.get_penalty())
        errLog.update(err, misc)
        

        if (e_i - epsilon) <= e_goal <= (e_i + epsilon):
            break

        if e_i > e_goal: 
            break

        if e_i < e_goal:
            
            gradient.reset()
            
            for clr_i in CLRS:
                if clr_i in clrs:
                    for side in ('lo', 'hi'):
                        
                        f_prime = copy.deepcopy(f)
                        f_prime.set_delta(side = side, clr = clr_i, val = -1)
                        
                        e_prime = tracked_shapes(img, 
                                  ( f_prime.get_threshLo(np=True) 
                                   ,f_prime.get_threshHi(np=True) ) 
                                   )
                                            
                        gradient.set(side = side, clr = clr_i, val = e_prime - e_i)
            
            gradient_ind = gradient.get_best(steep = steep, x_end = f.get_x_end()
                                            ,randomize = False)
            
            if log.b_log: 
                log.update( (_t, e_i, err, f.get_threshLo(), f.get_threshHi()
                            ,gradient.get_data(), gradient_ind, f.get_penalty() 
                           ) ) 

            f.set_delta(side = gradient_ind[0], clr = gradient_ind[1], val = -1)
            
    if kwargs.get('quick_return', False):
        return errLog.pop()

    if log.b_log: errLog.add_log(log.get_data())
    return errLog.get_data()


def iterThreshWrapper(img,**kwargs):
    pass

if __name__ == "__main__":


    def print_results3(data, full = False, round_places = 3, short = (1,2,3,4,5)):
        r_data = []
        for d in data[1]:
            try:
                r_data.append( round(d,round_places) )
            except:
                r_data.append( d )
        if full:
            return str(r_data)
        short_data = [r_data[i] for i in range(len(r_data)) if i in short]
        return str(short_data)

    def print_debug(data, full = False, round_places = 3, short = (1,2,3,4,5)
                    ,rounders = (1,2,5)):
        if len(data) < 2:
            return str(data)
        r_data = []
        for row in data:
            temp_row = []
            for i,elem in enumerate(row):
                try:
                    if i in rounders:
                        
                        temp_row.append( round(elem,round_places) )
                    else:
                        temp_row.append( elem )
                except:                   
                    try:
                        temp_e = []
                        for e in elem:
                            temp_e.append( round(e,round_places) )
                        temp_row.append(temp_e)
                    except:
                        temp_row.append( elem ) 
            if not(full):
                temp_row = [temp_row[i] for i in range(len(temp_row)) if i in short]            
            r_data.append(temp_row)
        return "\n".join([str(s) for s in r_data])

    #RUN TESTS -------------------------------------------------



    ## Steep Vs. Flat

    p = "../data/write/july/imgs17/img1.jpg"
    img = cv2.imread(p)

    out = iterThreshA(img, clrs = (0,1,2), goal_pct = 0.90, b_log = True 
                ,max_iter = 100, steep = True)
    print 'Steep 90pct: ', print_results3(out, round_places = 5)
    print 'Debug:------------------------ \n', 
    print print_debug(out[2], full = False, short = (1,3,4,5,6))
    print '\n'
    
    out = iterThreshA(img, clrs = (0,1,2), goal_pct = 0.90, b_log = True
                ,max_iter = 300, steep = False)
    print 'Flat 90pct: ', print_results3(out, round_places = 5)
    print 'Debug: (iters 0 to 5) -------- \n', 
    print print_debug(out[2][:5], full = False, short = (1,3,4,5,6))
    print '\n'

    ## How far you can go with the Ball

    p = "../data/write/july/imgs17/rect1.jpg"
    img = cv2.imread(p)
    
    out = iterThreshA(img, clrs = (0,1,2), goal_pct = 0.90, b_log = True
                ,max_iter = 300, steep = False)    
    print 'Flat 90 on Ball: ', print_results3(out, round_places = 5)
    print 'Debug: (iters 30 to 35) -------- \n', 
    print print_debug(out[2][30:35], full = False, short = (1,3,4,5,6))
    print '\n'

    ## Seperate Colors

    out = iterThreshA(img, clrs = (0,), goal_pct = 0.90, b_log = True
                ,max_iter = 300, steep = False)    
    print 'Color0 90 on Ball: ', print_results3(out, round_places = 5)
    print 'Debug: (iters 0 to 5) -------- \n', 
    print print_debug(out[2][:5], full = False, short = (1,3,4,5,6))
    print '\n'

    out = iterThreshA(img, clrs = (1,), goal_pct = 0.90, b_log = True
                ,max_iter = 300, steep = False)    
    print 'Color1 90 on Ball: ', print_results3(out, round_places = 5)
    print 'Debug: (iters 0 to 5) -------- \n', 
    print print_debug(out[2][:5], full = False, short = (1,3,4,5,6))
    print '\n'

    out = iterThreshA(img, clrs = (2,), goal_pct = 0.90, b_log = True
                ,max_iter = 300, steep = False)    
    print 'Color2 90 on Ball: ', print_results3(out, round_places = 5)
    print 'Debug: (iters 0 to 5) -------- \n', 
    print print_debug(out[2][:5], full = False, short = (1,3,4,5,6))
    print '\n'

    out = iterThreshA(img, clrs = (0,2), goal_pct = 0.90, b_log = True
                ,max_iter = 300, steep = False)    
    print 'Color-0and2 90 on Ball: ', print_results3(out, round_places = 5)
    print 'Debug: (iters 0 to 5) -------- \n', 
    print print_debug(out[2][:5], full = False, short = (1,3,4,5,6))
    print '\n'

    #standard output
    out = iterThreshA(img, clrs = (0,2), goal_pct = 0.90, b_log = False
                ,max_iter = 300, steep = False)    
    print 'b_log=F pretty out: ', print_results3(out, round_places = 5)
    print 'standard out', str(out)
    print '\n'
    
    d = []
    d.append( ((100,100,100),(200,200,200)))
    d.append( ((100,99,100),(200,20,205)))
    d.append( ((98,102,100),(200,200,20)))
    out = combine_threshes(d)
    print 'combined_thresh: ', str(out), '\n'

    img_p  = "C:/Users/wsutt/Desktop/files/ppd/ppd/data/write/july/imgs21/img1.jpg"
    back_img = cv2.imread(img_p)

    out = iterThreshB(back_img.copy(), init_thresh =  [[25, 97, 22], [70, 150, 82]],
                        clrs = (0,1,2), e_goal = 10.0, b_log = True
                        ,max_iter = 300, steep = False)    
    # print str(out)[:20]
    print 'example iterThreshB 90 on Background: ', print_results3(out, round_places = 5)
    print 'Debug: (iters 0 to 5) -------- \n', 
    print print_debug(out[2][:5], full = False, short = (1,3,4,5,6))
    len_debug = len(out[2])
    print 'length of debug out: ', str(len_debug)
    print print_debug(out[2][len_debug-10:len_debug], full = False, short = (1,3,4,5,6))
    print '\n'