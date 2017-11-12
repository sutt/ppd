import random, os, sys
import numpy as np
import threading
import Tkinter as tk
import Globals


def cmd_quit():
    Globals.gui_cmd_quit = True

def cmd_sw_agenda():
    Globals.sw_agenda = True

def cmd_gui_reset_agenda():
    Globals.gui_cmd_reset_agenda = True

def cmd_set_thresh_pct(sv):
    Globals.thresh_pct = round(float(sv.get()),3)

def cmd_gui_combine():
    Globals.gui_cmd_combine = True

def cmd_gui_set_rgb():
    Globals.gui_cmd_set_rgb = True

def cmd_gui_set_hsv():
    Globals.gui_cmd_set_hsv = True

# Helper Utils for build_thresh_gui ------------------------
# sv: stringvar, sf: subframe, fr: frame, v: intvar

def generate_sv():
    return [tk.StringVar() for i in range(6)]

def generate_sf(fr):
    return [tk.Frame(fr) for i in range(3)]

def pack_sf(sf):
    for _sf in sf:
        _sf.pack(side=tk.TOP)

def add_entries(sv, sf):
    for clr_i in range(3):
        txt_i =  [tk.Entry(sf[clr_i],textvariable = sv[clr_i*2 + i] 
                        ,width = 4).pack(side=tk.LEFT) 
                  for i in range(2)]

def add_cmd_btns(typ, sv, sf):
    tk.Button(sf, text = 'refresh',
              command = lambda: set_gui_to_thresh(typ,sv) ).pack(side=tk.LEFT)
    tk.Button(sf, text = 'set',
              command = lambda: set_thresh_from_gui(typ,sv) ).pack(side=tk.LEFT)

def set_gui_to_thresh(typ, sv):
    _thresh = []
    for i in range(6):
        if typ == 'rgb':
            _val = Globals.threshLoRgb[i/2] if (i % 2 == 0) else Globals.threshHiRgb[i/2]
        elif typ == 'hsv':
            _val = Globals.threshLoHsv[i/2] if (i % 2 == 0) else Globals.threshHiHsv[i/2]
        _thresh.append(_val)
    for i in range(6):
        sv[i].set(_thresh[i])

def set_thresh_from_gui(typ, sv):
        _threshLo = []
        _threshHi = []
        for clr_i in range(3):
            for i in range(2):
                if i == 0:
                    _threshLo.append(int(sv[clr_i*2 + i].get()))
                else:
                    _threshHi.append(int(sv[clr_i*2 + i].get()))
        if typ == 'rgb':
            Globals.threshLoRgb = np.array( _threshLo, dtype = 'uint8' )
            Globals.threshHiRgb = np.array( _threshHi, dtype = 'uint8' )
        elif typ == 'hsv':
            Globals.threshLoHsv = np.array( _threshLo, dtype = 'uint8' )
            Globals.threshHiHsv = np.array( _threshHi, dtype = 'uint8' )

def build_thresh_gui(typ, fr):
    tk.Label(fr, text="Current Thresh:").pack(side=tk.TOP)
    sv = generate_sv()
    set_gui_to_thresh(typ = typ ,sv = sv)
    sf = generate_sf(fr)
    pack_sf(sf)
    add_entries(sv, sf)
    sf2 = tk.Frame(fr)
    sf2.pack(side=tk.TOP)
    add_cmd_btns(typ, sv, sf2)

def update_b_thresh(typ, v):
    if typ == 'rgb':
        Globals.b_thresh_rgb = bool(v.get())
    if typ == 'hsv':
        Globals.b_thresh_hsv = bool(v.get())
    
        
def generate_radio_v():
    return tk.IntVar()
    
def build_radio_opt(v,fr, typ):
    
    if typ == 'rgb':
        v.set(int(Globals.b_thresh_rgb))
    if typ == 'hsv':
        v.set(int(Globals.b_thresh_hsv))

    tk.Radiobutton(fr, text="Off",variable=v,value=0,
            command=lambda: update_b_thresh(typ,v)).pack(side=tk.LEFT)

    tk.Radiobutton(fr, text="On",variable=v, value=1,
            command=lambda: update_b_thresh(typ,v)).pack(side=tk.LEFT)


def build_gui_a(root):
    
    f1 = tk.Frame(root)
    f1.pack(side = tk.TOP)

    tk.Button(f1, text = 'quit!',
                        command = cmd_quit).pack()

    #AGENDA
    f1a = tk.Frame(root)
    f1a.pack(side = tk.TOP)
    
    tk.Label(f1a, text="Agenda Cmds:").pack(side=tk.TOP)

    f1a1 = tk.Frame(f1a)
    f1a1.pack(side = tk.TOP)

    tk.Button(f1a1, text = 'next step',
                        command = cmd_sw_agenda).pack(side=tk.LEFT)

    tk.Button(f1a1, text = 'reset',
                        command = cmd_sw_agenda).pack(side=tk.LEFT)

    f1a2 = tk.Frame(f1a)
    f1a2.pack(side = tk.TOP)

    tk.Label(f1a2, text="thresh pct:").pack(side=tk.LEFT)

    sv_tp = tk.StringVar()
    sv_tp.set(str(Globals.thresh_pct))
    tk.Entry(f1a2,textvariable = sv_tp, width = 6 ).pack(side=tk.LEFT)

    tk.Button(f1a2, text = 'set', command = lambda: cmd_set_thresh_pct(sv_tp)
                ).pack(side=tk.LEFT)

    tk.Button(f1a2, text = 'run iterA', 
                    command = cmd_gui_combine
                    ).pack(side=tk.LEFT)
    

    #OUTPUT BOXES
    f1a3a = tk.Frame(f1a)
    f1a3a.pack(side = tk.TOP)

    tk.Label(f1a3a, text="output rgb:").pack(side=tk.LEFT)

    
    Globals.sv_t1 = tk.StringVar()
    tk.Entry(f1a3a,textvariable = Globals.sv_t1, width = 20 ).pack(side=tk.LEFT)
    tk.Button(f1a3a, text = 'set', 
                    command = cmd_gui_set_rgb
                    ).pack(side=tk.LEFT)

    f1a3b = tk.Frame(f1a)
    f1a3b.pack(side = tk.TOP)

    tk.Label(f1a3b, text="output hsv:").pack(side=tk.LEFT)

    sv_t2 = tk.StringVar()
    tk.Entry(f1a3b,textvariable = sv_t2, width = 20 ).pack(side=tk.LEFT)
    tk.Button(f1a3b, text = 'set', 
                    command = cmd_gui_set_hsv
                    ).pack(side=tk.LEFT)
    #THRESHES
    f2 = tk.Frame(root)
    f2.pack(side = tk.TOP)

    label = tk.Label(f2, text="RGB Thresh:").pack()
    
    v_rgb = generate_radio_v()
    build_radio_opt(v_rgb, f2, typ = 'rgb')

    f3 = tk.Frame(root)
    f3.pack(anchor=tk.W)
    build_thresh_gui(typ='rgb',fr = f3)

    f4 = tk.Frame(root)
    f4.pack(side = tk.TOP)

    label = tk.Label(f4, text="HSV Thresh:").pack()
    
    v_hsv = generate_radio_v()
    build_radio_opt(v_hsv, f4, typ = 'hsv')

    f4 = tk.Frame(root)
    f4.pack(anchor=tk.W)
    build_thresh_gui(typ='hsv',fr = f4)

    return root


class GuiA(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.start()

    def callback(self):
        self.root.quit()

    def run(self):
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.callback)
        self.root = build_gui_a(self.root)
        self.root.mainloop()
