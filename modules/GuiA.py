import random, os, sys
import threading
import Tkinter as tk
import Globals


def random_pass():
    Globals.gui_pass1 = int(random.uniform(0,10))


def build_gui_a(root):
    
    label = tk.Label(root, text="RGB Thresh:")
    label.pack()

    v = tk.IntVar
    v = int(Globals.b_thresh_rgb)

    def set_rgb_thresh_bool():
        Globals.b_thresh_rgb = bool(v)

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
