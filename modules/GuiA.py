import random, os, sys
import threading
import Tkinter as tk
import Globals

def random_pass():
    Globals.gui_pass1 = int(random.uniform(0,10))

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

def build_gui_a(root):
    
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

    tk.Button(root, text = 'random digit print',
                        command = random_pass).pack()
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
