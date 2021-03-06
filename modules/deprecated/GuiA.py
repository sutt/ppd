import random, os, sys
import numpy as np
import threading
import Tkinter as tk
import Globals


class GlobeGui():

    def __init__(self):
        self.sv_rgb = None
        self.sv_hsv = None
        self.sv_output_rgb = None
        self.sv_output_hsv = None
        self.sv_track_blur = None
        self.sv_track_repair_iters = None

    def generate_sv(self, typ):
        if typ == 'rgb':
            self.sv_rgb =  [tk.StringVar() for i in range(6)]
        if typ == 'hsv':
            self.sv_hsv =  [tk.StringVar() for i in range(6)]

    def generate_sv_output(self,typ):
        if typ == 'rgb':
            self.sv_output_rgb =  tk.StringVar()
        if typ == 'hsv':
            self.sv_output_hsv =  tk.StringVar()

    def generate_sv_track_blur(self):
        self.sv_track_blur = tk.StringVar()
        
    def generate_sv_track_repair_iters(self):
        self.sv_track_repair_iters = tk.StringVar()

    def get_sv_output(self,typ):
        if typ == 'rgb':
            return self.sv_output_rgb
        if typ == 'hsv':
            return self.sv_output_hsv

    def get_sv(self,typ):
        if typ == 'rgb':
            return self.sv_rgb
        if typ == 'hsv':
            return self.sv_hsv
    
    def get_sv_track_blur(self):
        return self.sv_track_blur

    def get_sv_track_repair_iters(self):
        return self.sv_track_repair_iters

    def set_gui_to_thresh(self,typ):
        _thresh = []
        for i in range(6):
            if typ == 'rgb':
                _val = Globals.threshLoRgb[i/2] if (i % 2 == 0) else Globals.threshHiRgb[i/2]
            elif typ == 'hsv':
                _val = Globals.threshLoHsv[i/2] if (i % 2 == 0) else Globals.threshHiHsv[i/2]
            _thresh.append(_val)
        for i in range(6):
            if typ == 'rgb':
                self.sv_rgb[i].set(_thresh[i])
            elif typ == 'hsv':
                self.sv_hsv[i].set(_thresh[i])

    def set_gui_to_output(self, threshes):
        self.sv_output_rgb.set("".join([str(_t.tolist()) for _t in threshes[0]]))
        self.sv_output_hsv.set("".join([str(_t.tolist()) for _t in threshes[1]]))

    def set_gui_to_track_blur(self,blur_amt):
        if ((int(blur_amt) % 2) == 0):
            print 'blur_amt ', str(blur_amt), ' is even. must be odd' 
            return
        self.sv_track_blur.set( blur_amt)

    def set_gui_to_track_repair_iters(self, iters_amt):
        self.sv_track_repair_iters.set(str(iters_amt))

globeGui = GlobeGui()

def cmd_quit():
    Globals.gui_cmd_quit = True

def cmd_sw_agenda():
    Globals.sw_agenda = True

def cmd_gui_reset_agenda():
    Globals.gui_cmd_reset_agenda = True

def cmd_set_thresh_pct(sv):
    Globals.thresh_pct = round(float(sv.get()),3)

def cmd_set_max_width(sv):
    Globals.max_width_to_expand = int(sv.get())

def cmd_gui_combine():
    Globals.gui_cmd_combine = True

def cmd_gui_expand():
    Globals.gui_cmd_expand = True

def cmd_gui_set_rgb():
    Globals.gui_cmd_set_rgb = True
    #globeGui.set_gui_to_thresh(typ = 'rgb')

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
    globeGui.generate_sv(typ = typ)
    sv = globeGui.get_sv(typ = typ)
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
    if typ == 'display_info':
        Globals.gui_track_success = bool(v.get())
    if typ == 'display_big_circle':
        Globals.gui_big_tracking_circle = bool(v.get())
    if typ == 'camera_num':
        Globals.gui_camera_num = int(v.get())
        Globals.gui_camera_reset = True
    if typ == 'camera_size_enum':
        Globals.gui_camera_size_enum = int(v.get())
        Globals.gui_camera_reset = True
    if typ == 'picamera_enum':
        Globals.gui_picamera_enum = int(v.get())
        Globals.gui_camera_reset = True

def set_track_blur_from_gui(blur_amt):
    if ((int(blur_amt) % 2) == 0):
            print 'blur_amt ', str(blur_amt), ' is even. must be odd' 
            return
    Globals.param_tracking_blur = int(blur_amt)

def set_track_repair_iters_from_gui(iters_amt):
    Globals.param_tracking_repair_iters = int(iters_amt)

def generate_radio_v():
    return tk.IntVar()
    
def build_radio_opt(v,fr, typ):
    
    if typ == 'rgb':
        v.set(int(Globals.b_thresh_rgb))
    if typ == 'hsv':
        v.set(int(Globals.b_thresh_hsv))
    if typ == 'display_info':
        v.set(int(0)) 
    if typ == 'display_big_circle':
        v.set(int(0)) 

    tk.Radiobutton(fr, text="Off",variable=v,value=0,
            command=lambda: update_b_thresh(typ,v)).pack(side=tk.LEFT)

    tk.Radiobutton(fr, text="On",variable=v, value=1,
            command=lambda: update_b_thresh(typ,v)).pack(side=tk.LEFT)

def build_radio_opt_multi(v,fr, typ, texts):
    
    if typ == 'camera_num':
        v.set(int(Globals.gui_camera_num))
    if typ == 'camera_size':
        v.set(int(Globals.gui_camera_size_enum))
    if typ == 'picamera_enum':
        v.set(int(Globals.gui_picamera_enum))


    tk.Radiobutton(fr, text=texts[0],variable=v,value=0,
            command=lambda: update_b_thresh(typ,v)).pack(side=tk.LEFT)

    tk.Radiobutton(fr, text=texts[1],variable=v, value=1,
            command=lambda: update_b_thresh(typ,v)).pack(side=tk.LEFT)

    tk.Radiobutton(fr, text=texts[2],variable=v, value=2,
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
                        command = cmd_gui_reset_agenda).pack(side=tk.LEFT)

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

    f1a3 = tk.Frame(f1a)
    f1a3.pack(side = tk.TOP)

    tk.Label(f1a3, text="max width:").pack(side=tk.LEFT)

    Globals.max_width_to_expand = 10
    sv_tp2 = tk.StringVar()
    sv_tp2.set(str(Globals.max_width_to_expand))
    tk.Entry(f1a3,textvariable = sv_tp2, width = 6 ).pack(side=tk.LEFT)

    tk.Button(f1a3, text = 'set', command = lambda: cmd_set_max_width(sv_tp2)
                ).pack(side=tk.LEFT)

    tk.Button(f1a3, text = 'run iterb', 
                    command = cmd_gui_expand
                    ).pack(side=tk.LEFT)
    

    #OUTPUT BOXES
    f1a3a = tk.Frame(f1a)
    f1a3a.pack(side = tk.TOP)

    tk.Label(f1a3a, text="output rgb:").pack(side=tk.LEFT)

    globeGui.generate_sv_output(typ = 'rgb')
    sv_t1 = globeGui.get_sv_output(typ = 'rgb')
    tk.Entry(f1a3a,textvariable = sv_t1, width = 24 ).pack(side=tk.LEFT)
    tk.Button(f1a3a, text = 'set', 
                    command = cmd_gui_set_rgb
                    ).pack(side=tk.LEFT)

    f1a3b = tk.Frame(f1a)
    f1a3b.pack(side = tk.TOP)

    tk.Label(f1a3b, text="output hsv:").pack(side=tk.LEFT)
    
    globeGui.generate_sv_output(typ = 'hsv')
    sv_t2 = globeGui.get_sv_output(typ = 'hsv')
    tk.Entry(f1a3b,textvariable = sv_t2, width = 24 ).pack(side=tk.LEFT)
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

    #TRACKING PARAMS
    f5 = tk.Frame(root)
    f5.pack(anchor=tk.W)
    
    tk.Label(f5, text="tracking blur:").pack(side=tk.LEFT)
    globeGui.generate_sv_track_blur()
    sv_tb = globeGui.get_sv_track_blur()
    tk.Entry(f5,textvariable = sv_tb, width = 8 ).pack(side=tk.LEFT)
    globeGui.set_gui_to_track_blur(str(Globals.param_tracking_blur))
    tk.Button(f5, text = 'set', 
                  command = lambda: set_track_blur_from_gui(sv_tb.get()  )
                    ).pack(side=tk.LEFT)
    
    tk.Label(f5, text="repair iters:").pack(side=tk.LEFT)
    globeGui.generate_sv_track_repair_iters()
    sv_ri = globeGui.get_sv_track_repair_iters()
    tk.Entry(f5,textvariable = sv_ri, width = 8 ).pack(side=tk.LEFT)
    globeGui.set_gui_to_track_repair_iters(str(Globals.param_tracking_repair_iters))
    tk.Button(f5, text = 'set', 
                  command = lambda: set_track_repair_iters_from_gui(sv_ri.get()  )
                    ).pack(side=tk.LEFT)

    #DISPLAY PARAMS
    f6 = tk.Frame(root)
    f6.pack(anchor=tk.W)

    f6a = tk.Frame(f6)
    f6a.pack(side = tk.TOP)
    tk.Label(f6a, text="display info:").pack(side=tk.LEFT)
    v_display_info = generate_radio_v()
    build_radio_opt(v_display_info, f6a, typ = 'display_info')

    f6b = tk.Frame(f6)
    f6b.pack(side = tk.TOP)
    tk.Label(f6b, text="display mask big circle:").pack(side=tk.LEFT)
    v_display_big_circle = generate_radio_v()
    build_radio_opt(v_display_big_circle, f6b, typ = 'display_big_circle')

    # f6b = tk.Frame(f6)
    # f6b.pack(side = tk.TOP)
    # tk.Label(f6b, text="display mask big circle:").pack(side=tk.LEFT)
    # v_display_big_circle = generate_radio_v()
    # build_radio_opt(v_display_big_circle, f6b, typ = 'display_big_circle')

    #CAMERA PARAMS
    f7 = tk.Frame(root)
    f7.pack(anchor=tk.W)

    f7a = tk.Frame(f7)
    f7a.pack(side = tk.TOP)
    tk.Label(f7a, text="camera num:").pack(side=tk.LEFT)
    v_camera_num = generate_radio_v()
    build_radio_opt_multi(v_camera_num, f7a, typ = 'camera_num' 
                         ,texts = ["0","1","2"])

    f7b = tk.Frame(f7)
    f7b.pack(side = tk.TOP)
    tk.Label(f7b, text="camera size:").pack(side=tk.LEFT)
    v_camera_num = generate_radio_v()
    build_radio_opt_multi(v_display_info, f7b, typ = 'camera_size_enum' 
                         ,texts = ["640","1280","1920"])

    f7c = tk.Frame(f7)
    f7c.pack(side = tk.TOP)
    tk.Label(f7c, text="picamera:").pack(side=tk.LEFT)
    v_picamera_num = generate_radio_v()
    build_radio_opt_multi(v_picamera_num, f7c, typ = 'picamera_enum' 
                         ,texts = ["off","on main","on sub"])

    return root


class GuiA(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.start()
        self.globeGui = globeGui

    def callback(self):
        self.root.quit()

    def run(self):
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.callback)
        self.root = build_gui_a(self.root)
        self.root.mainloop()
