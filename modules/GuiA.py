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


    

def build_dialog_1(root, input_global):
    
    v = tk.IntVar
    v = int(input_global)

    def update_func():
        input_global = bool(v)

    tk.Radiobutton(root, 
            text="Off",
            variable=v, 
            value=0,
            command=update_func).pack(anchor=tk.W)
    tk.Radiobutton(root, 
            text="On",
            variable=v, 
            value=1,
            command=update_func).pack(anchor=tk.W)

    return root

def build_gui_b(root):
    
    f1 = tk.Frame(root)
    f1.pack(side = tk.TOP)

    tk.Button(f1, text = 'start agenda',
                        command = cmd_sw_agenda).pack()

    tk.Button(f1, text = 'quit!',
                        command = cmd_quit).pack()
    
    f2 = tk.Frame(root)
    f2.pack(side = tk.TOP)

    label = tk.Label(f2, text="RGB Thresh:").pack()
    
    v = tk.IntVar()
    v.set(int(Globals.b_thresh_rgb))
    def set_rgb_thresh_bool():
        Globals.b_thresh_rgb = bool(v.get())

    tk.Radiobutton(f2, 
            text="Off",
            variable=v, 
            value=0,
            command=set_rgb_thresh_bool).pack(side=tk.LEFT)
    tk.Radiobutton(f2, 
            text="On",
            variable=v, 
            value=1,
            command=set_rgb_thresh_bool).pack(side=tk.LEFT)

    f3 = tk.Frame(root)
    f3.pack(anchor=tk.W)
    build_thresh_gui(typ='rgb',fr = f3)

    # tk.Label(f3, text="Current Thresh:").pack(side=tk.TOP)    

    # # sv1 = [tk.StringVar() for i in range(6)]
    # sv = generate_sv()
    
    # # def set_gui_to_thresh():
    # #     _thresh = []
    # #     for i in range(6):
    # #         _val = Globals.threshLoRgb[i/2] if (i % 2 == 0) else Globals.threshHiRgb[i/2]
    # #         _thresh.append(_val)
    # #     for i in range(6):
    # #         sv1[i].set(_thresh[i])

    # set_gui_to_thresh(type='rgb',sv_t = sv )

    # # sf1 = [tk.Frame(f3) for i in range(3)]
    # sf = generate_sf()
    # pack_sf(sf)
    # # for _sf in sf1:
    # #     _sf.pack(side=tk.TOP)

    # for clr_i in range(3):
    #     txt_i =  [tk.Entry(sf1[clr_i],textvariable = sv1[clr_i*2 + i] 
    #                        ,width = 4).pack(side=tk.LEFT) 
    #              for i in range(2)]

    # f3d = tk.Frame(f3)
    # f3d.pack(side=tk.TOP)

    # tk.Button(f3d, text = 'refresh',
    #           command = set_gui_to_thresh).pack(side=tk.LEFT)
    
    # def set_thresh_from_gui():
    #     _threshLo = []
    #     _threshHi = []
    #     for clr_i in range(3):
    #         for i in range(2):
    #             if i == 0:
    #                 _threshLo.append(int(sv1[clr_i*2 + i].get()))
    #             else:
    #                 _threshHi.append(int(sv1[clr_i*2 + i].get()))
    #     print 'threshLo ', str(_threshLo)
    #     print 'threshHi ', str(_threshHi)
    #     Globals.threshLoRgb = np.array( _threshLo, dtype = 'uint8' )
    #     Globals.threshHiRgb = np.array( _threshHi, dtype = 'uint8' )

    
    # # TODO - add set_thresh_from_gui
    # tk.Button(f3d, text = 'set',
    #           command = set_thresh_from_gui).pack(side=tk.LEFT)

    return root

def build_gui_a(root):
    
    tk.Button(root, text = 'start agenda',
                        command = cmd_sw_agenda).pack()

    tk.Button(root, text = 'quit!',
                        command = cmd_quit).pack()
    
    label = tk.Label(root, text="RGB Thresh:").pack()
    v = tk.IntVar()
    v.set(int(Globals.b_thresh_rgb))
    def set_rgb_thresh_bool():
        Globals.b_thresh_rgb = bool(v.get())

    tk.Radiobutton(root, 
            text="Off",
            variable=v, 
            value=0,
            command=set_rgb_thresh_bool).pack(anchor=tk.W)
    tk.Radiobutton(root, 
            text="On",
            variable=v, 
            value=1,
            command=set_rgb_thresh_bool).pack(anchor=tk.W)

    tk.Label(root, text="Blue/Green/Red:").pack(anchor=tk.W)    

    rgb1_strvar = tk.StringVar()
    rgb2_strvar = tk.StringVar()
    rgb3_strvar = tk.StringVar()
    rgb1_strvar.set(str(Globals.threshLoRgb[0]))    
    def set_rgb_cmd():
        Globals.gui_pass1 = int(rgb1_strvar.get())

    LF1 = tk.Frame(root).pack(anchor = tk.W)

    tk.Entry(LF1,textvariable = rgb1_strvar 
            , width = 4).pack(anchor=tk.W)
    tk.Entry(LF1,textvariable = rgb2_strvar 
            , width = 4).pack(anchor = tk.W)
    tk.Entry(LF1,textvariable = rgb3_strvar 
            , width = 4).pack(anchor = tk.W)
    
    # tk.Entry(root,textvariable = rgb1_strvar 
    #         , width = 4).pack(side = tk.LEFT)
    # tk.Entry(root,textvariable = rgb2_strvar 
    #         , width = 4).pack(side = tk.LEFT)
    # tk.Entry(root,textvariable = rgb3_strvar 
    #         , width = 4).pack(side = tk.LEFT)

    # tk.Entry(root,textvariable = rgb2_strvar).pack(anchor = tk.E)
            

    tk.Button(root, text = 'set rgb thresh',
                        command = set_rgb_cmd).pack(anchor = tk.W)

    tk.Label(root, text="HSV Thresh:").pack()    
    v2 = tk.IntVar()
    v2.set(int(Globals.b_thresh_hsv))
    def set_hsv_thresh_bool():
        Globals.b_thresh_hsv = bool(v2.get())

    tk.Radiobutton(root, 
            text="Off",
            variable=v2, 
            value=0,
            command=set_hsv_thresh_bool).pack(anchor=tk.W)
    tk.Radiobutton(root, 
            text="On",
            variable=v2, 
            value=1,
            command=set_hsv_thresh_bool).pack(anchor=tk.W)

    #root = build_dialog_1(root, Globals.b_thresh_hsv)

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
        self.root = build_gui_b(self.root)
        self.root.mainloop()
