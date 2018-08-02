import random, os, sys
import threading
import Tkinter as tk
import GlobalsB as Globals


class GuiData:

    def __init__(self):
        self.record_on = False
        self.sv_fn = None

class BuildGuiB:

    def __init__(self, b_log=False):
        self.record_button = None
        self.b_log = b_log

    def cmd_quit(self):
        Globals.gui_cmd_quit = True

    def cmd_record_sw(self):
        ''' toggle gui_cmd_record global; reformat record button color '''
        if Globals.gui_cmd_record:
            Globals.gui_cmd_record = False
            self.record_button.configure(bg = 'gray')
        else:
            Globals.gui_cmd_record = True
            self.record_button.configure(bg = '#000fff000')
        if self.b_log:
            print 'gui_cmd_record: ', str(Globals.gui_cmd_record)
        
    def get_sv_fn(self):
        ''' unique filename entry box -> global '''
        Globals.gui_unique_fn = str(self.sv_fn.get())
        if self.b_log:
            print 'setting gui_unique_fn to: ', Globals.gui_unique_fn

    def set_sv_fn(self, fn):
        ''' unqiue filename entry box, set value displayed in gui '''
        self.sv_fn.set(str(fn))
        if self.b_log:
            print 'setting sv_fn to: ', str(fn)
        

    def build_gui_b(self, root):
        
        f1 = tk.Frame(root)
        f1.pack(side = tk.TOP)
        tk.Button(
             f1
            ,text = 'quit'
            ,command = self.cmd_quit
            ).pack()
        f1a = tk.Frame(root)
        f1a.pack(side = tk.TOP)

        self.record_button = tk.Button(
                f1a
                ,text = 'record toggle'
                ,bg = 'gray'
                ,command = self.cmd_record_sw
                )
        self.record_button.pack()

        f1a2 = tk.Frame(f1a)
        f1a2.pack(side = tk.TOP)
        
        tk.Label(
                f1a2
                ,text="filename:"
            ).pack(side=tk.LEFT)
        
        self.sv_fn = tk.StringVar()
        self.set_sv_fn(Globals.gui_unique_fn)
        
        self.fn_entry = tk.Entry(
                f1a2
                ,textvariable = self.sv_fn
                ,width = 16
                )
        self.fn_entry.pack(side=tk.LEFT)
        
        tk.Button(
                f1a2
                ,text = 'set'
                ,command = self.get_sv_fn
            ).pack(side=tk.LEFT)

        return root

class GuiB(threading.Thread):
    
    def __init__(self, b_log=False):
        threading.Thread.__init__(self)
        self.start()
        self.myGui = BuildGuiB(b_log=b_log)
        # self.globeGui = globeGui

    def callback(self):
        self.root.quit()

    def run(self):
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.callback)
        self.root = self.myGui.build_gui_b(self.root)
        self.root.mainloop()



if __name__ == "__main__":

    Globals.init()
    Globals.gui_cmd_quit = False
    Globals.gui_cmd_record = False
    Globals.gui_cmd_reset = False
    Globals.gui_unique_fn = "------N/A------"
    
    gui = GuiB(b_log=True)