import random, os, sys
import numpy as np
import threading
import Tkinter as tk
import Globals



def cmd_sw_agenda():
    Globals.gui_cmd_sw_agenda = True

def cmd_quit():
    Globals.gui_cmd_quit = True

# Helper Utils for build_thresh_gui
# sv: stringvar, sf: subframe, fr: frame

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
    
    # v = tk.IntVar()
    
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

    tk.Button(f1, text = 'start agenda',
                        command = cmd_sw_agenda).pack()

    tk.Button(f1, text = 'quit!',
                        command = cmd_quit).pack()
    
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
