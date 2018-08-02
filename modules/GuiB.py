import random, os, sys
import threading
import Tkinter as tk
import GlobalsB as Globals

# Globals.init()
# Globals.gui_pass1 = 0
# Globals.gui_cmd_quit = False

class GuiData:

    def __init__(self):
        self.record_on = False

def cmd_quit():
    Globals.gui_cmd_quit = True

def cmd_record_sw():
    if Globals.gui_cmd_record:
        Globals.gui_cmd_record = False
    else:
        Globals.gui_cmd_record = True

def build_gui_b(root):
    
    f1 = tk.Frame(root)
    f1.pack(side = tk.TOP)
    tk.Button(f1
             ,text = 'quit!'
             ,command = cmd_quit
             ).pack()

    f1a = tk.Frame(root)
    f1a.pack(side = tk.TOP)
    tk.Button(f1a
             ,text = 'record toggle'
             ,command = cmd_record_sw
             ).pack()




    
    return root

class GuiB(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.start()
        # self.globeGui = globeGui

    def callback(self):
        self.root.quit()

    def run(self):
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.callback)
        self.root = build_gui_b(self.root)
        self.root.mainloop()