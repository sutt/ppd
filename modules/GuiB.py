import random, os, sys
import threading
import Tkinter as tk
import GlobalsB as Globals


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
    if b_log:
        print 'gui_cmd_record: ', str(Globals.gui_cmd_record)

class BuildGuiB:

    def __init__(self, b_log=False):
        self.record_button = None
        self.b_log = b_log

    def cmd_record_sw(self):
        if Globals.gui_cmd_record:
            Globals.gui_cmd_record = False
            self.record_button.configure(bg = 'gray')
        else:
            Globals.gui_cmd_record = True
            self.record_button.configure(bg = '#000fff000')
        if self.b_log:
            print 'gui_cmd_record: ', str(Globals.gui_cmd_record)
        

    def build_gui_b(self, root):
        
        f1 = tk.Frame(root)
        f1.pack(side = tk.TOP)
        tk.Button(f1
                ,text = 'quit!'
                ,command = cmd_quit
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
    
    gui = GuiB(b_log=True)