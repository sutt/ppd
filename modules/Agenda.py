import sys, os, random, time, copy
import Globals

def tf_gen(xy = (100,100), square_size = 50):
    xy2 = (xy[0] + square_size, xy[1] + square_size)
    return (xy,xy2)

def corners(img_wh, margins = 150, size = 50):
    w,h = img_wh[0], img_wh[1] 
    ret = []
    pad = margins + size
    ret.append( ((w - pad, h - pad), size) )
    ret.append( ((margins, h - pad), size) )
    ret.append( ((margins, margins), size) )
    ret.append( ((w - pad, margins), size) )
    return ret[:]

def middle(img_wh, size = 50):
    w,h = img_wh[0], img_wh[1] 
    w_mid, h_mid = int(w/2), int(h/2)
    rad = (size / 2)
    ret = []
    ret.append( ((w_mid - rad, h_mid - rad), size) )
    return ret[:]

def routineA(img_wh = (640,480), **kwargs):
    ret = []
    ret.extend( middle( img_wh,size = 80) )
    ret.extend( corners(img_wh,margins = 100, size = 80) )
    ret.extend( middle( img_wh,size = 50) )
    ret.extend( corners(img_wh,margins = 50, size = 50) )
    return ret

data = [ ((100,100), 50)
        ,((200,100), 50)
        ,((100,200), 50)
        ]

class AgendaA:

    def __init__(self, img_wh = (640,480)):
        self.seq_ind = 0
        self.img_wh = (640,480)
        self.track_frame_routine = routineA()
        

    def do_agenda(self, **kwargs):
        routine = self.track_frame_routine
        len_routine = len(routine)
        if len_routine - 1 < self.seq_ind:
            print 'Routine at End. Seq num: ', str(self.seq_ind)
        else:
            d = routine[self.seq_ind]
            Globals.current_tracking_frame = tf_gen(xy = d[0],square_size = d[1] )
            self.seq_ind += 1
            print 'New Tracking Frame: ', str(Globals.current_tracking_frame), ' seq_ind: ', str(self.seq_ind)
            