import sys, os, random, time, copy
import numpy as np
import Globals
from AppUtils import write_pic
from AppUtils import make_dir
from AppUtils import uni_dir
from IterThresh import combine_threshes
from IterThresh import iterThreshA
from ImgProcs import transformA


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

def routineB(img_wh = (640,480), **kwargs):
    ret = []
    ret.extend( middle( img_wh,size = 80) )
    ret.extend( corners(img_wh,margins = 100, size = 50) )
    return ret

data = [ ((100,100), 50)
        ,((200,100), 50)
        ,((100,200), 50)
        ]

class AgendaA:

    def __init__(self, img_wh = (640,480), **kwargs):
        self.seq_ind = 0
        self.img_wh = (640,480)
        self.track_frame_routine = routineB()
        self.rect_log = []
        self.backg_log = []
        self.seq_end = False
        self.sw_calcd_combined = False
        self.b_rgb_thresh = bool(kwargs.get('b_rgb_thresh', True))
        self.b_hsv_thresh = bool(kwargs.get('b_hsv_thresh', False))
        self.b_log_combine_proc = True
        self.combine_proc_log = []
        self.temp_thresh_rgb = None
        self.temp_thresh_hsv = None

        writepath = "data/write/oct"
        output_dir = uni_dir(writepath)
        self.output_dir = uni_dir(writepath)
        make_dir(writepath + "/" + output_dir)

    def timer(self):
        pass
            # if b_agenda_timer:
            #     if (sw_agenda == False) and sw_reset_agenda_timer:
            #         next_agenda_time = time.time() + 3.0
            #         sw_reset_agenda_timer = False

            #     elif time.time() > next_agenda_time:
            #         sw_agenda = True

            #     else:
            #         _temp = round(next_agenda_time - time.time(), 1)
            #         if _temp < 10: _temp = "*" * int(_temp * 2)
            #         info_annotations.append(_temp)

    def do_rect_move(self, **kwargs):
        routine = self.track_frame_routine
        len_routine = len(routine)
        if len_routine - 1 < self.seq_ind:
            if not(self.seq_end):
                print 'Routine at End. Seq num: ', str(self.seq_ind)
            self.seq_end = True
            
        else:
            d = routine[self.seq_ind]
            Globals.current_tracking_frame = tf_gen(xy = d[0],square_size = d[1] )
            self.seq_ind += 1
            print 'New Tracking Frame: ', str(Globals.current_tracking_frame), ' seq_ind: ', str(self.seq_ind)

    
    def write_rect_files(self, img, fname = "rect", **kwargs):
        fname = str(fname) + str(self.seq_ind)
        write_pic(img, name_base = fname, path=self.output_dir)

    def log_rect_imgs(self, img, **kwargs):
        self.rect_log.append(img)

    def write_backg_files(self, img, fname = "backg", **kwargs):
        fname = str(fname) + str(self.seq_ind)
        write_pic(img, name_base = fname, path=self.output_dir)

    def log_backg_imgs(self, img, **kwargs):
        self.backg_log.append(img)
        
    def combine_threshes(self, thresh_type = 'rgb', **kwargs):
        print 'starting combine thresh on : %s ' % thresh_type
        threshes = []
        
        for img in self.rect_log:
            
            if thresh_type == 'hsv':
                img = transformA(img.copy(), blur = 1, b_hsv = True)

            #transformA(frame, blur > 0) -> img_t
            out_thresh = iterThreshA( img
                                      ,goal_pct = Globals.thresh_pct 
                                      ,steep = False)

            _lo , _hi = out_thresh[1][3], out_thresh[1][4]
            threshes.append((_lo,_hi))

        if self.b_log_combine_proc:
            self.combine_proc_log.append(threshes)

        self.sw_calcd_combined = True
        
        all_lo, all_hi = combine_threshes(threshes)
        return all_lo, all_hi
    
    def apply_thresh(self, lo, hi, thresh_type = 'rgb'):
        if thresh_type == 'rgb':
            Globals.threshLoRgb = np.array( lo , dtype = 'uint8' )
            Globals.threshHiRgb = np.array( hi, dtype = 'uint8' )
            print 'Globals RGB set: ', str(Globals.threshLoRgb), str(Globals.threshHiRgb)
        elif thresh_type == 'hsv':
            Globals.threshLoHsv = np.array( lo , dtype = 'uint8' )
            Globals.threshHiHsv = np.array( hi, dtype = 'uint8' )
            print 'Globals HSV set: ', str(Globals.threshLoHsv), str(Globals.threshHiHsv)
        else:
            print 'Couldnt find thresh_type to set global thresh'

    def apply_thresh_2(self, thresh_type = 'rgb'):
        if thresh_type == 'rgb':
            lo, hi = self.temp_thresh_rgb[0], self.temp_thresh_rgb[1]
            Globals.threshLoRgb = np.array( lo , dtype = 'uint8' )
            Globals.threshHiRgb = np.array( hi, dtype = 'uint8' )
            print 'Globals RGB set: ', str(Globals.threshLoRgb), str(Globals.threshHiRgb)
        elif thresh_type == 'hsv':
            lo, hi = self.temp_thresh_hsv[0], self.temp_thresh_hsv[1]
            Globals.threshLoHsv = np.array( lo , dtype = 'uint8' )
            Globals.threshHiHsv = np.array( hi, dtype = 'uint8' )
            print 'Globals HSV set: ', str(Globals.threshLoHsv), str(Globals.threshHiHsv)
        else:
            print 'Couldnt find thresh_type to set global thresh'

    def print_logs(self, log_type = 'combine_proc'):

        if log_type == 'combine_proc':
            out = "\n".join([str(x) for x in self.combine_proc_log])
            print out
        else:
            print 'couldnt find the log to print.'

    def run_combine(self):
        
        _lo, _hi = self.combine_threshes(thresh_type = 'rgb')
        self.print_logs()
        self.temp_thresh_rgb = [_lo, _hi]

        _lo, _hi = self.combine_threshes(thresh_type = 'hsv')
        self.print_logs()
        self.temp_thresh_hsv = [_lo, _hi]
        #self.apply_thresh(_lo,_hi, thresh_type = 'hsv')

    def get_temp_threshes(self):
        return (self.temp_thresh_rgb, self.temp_thresh_hsv)

    def apply_agenda_threshes(self):
        pass
        


if __name__ == "__main__":
    
    agenda = AgendaA()
    agenda.b_log_combine_proc = True
    #agenda.combine_proc_log.append(iterThreshA())
