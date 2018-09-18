import random, os, sys
import threading
import Tkinter as tk
import GlobalsC as g


class GuiData:

    def __init__(self):
        self.record_on = False
        self.sv_fn = None

class BuildGuiC:

    def __init__(self, b_log=False):
        self.b_log = b_log
        self.record_button = None

    def cmd_retreat(self):
        g.switchRetreatFrame = True
        # print '--retreat'

    def cmd_advance(self):
        g.switchAdvanceFrame = True
        # print '--advance'

    def cmd_record_sw(self):
        ''' play/pause '''
        if g.playOn:
            g.playOn = False
            self.record_button.configure(bg = 'gray')
        else:
            g.playOn = True
            self.record_button.configure(bg = '#000fff000')
        
        

    def build_gui_c(self, root):
        

        f1a = tk.Frame(root)
        f1a.pack(side = tk.TOP)

        self.record_button = tk.Button(
                f1a
                ,text = 'play toggle'
                ,bg = 'gray'
                ,command = self.cmd_record_sw
                )
        self.record_button.pack()

        
        f1b = tk.Frame(root)
        f1b.pack(side = tk.TOP)
        
        tk.Button(
             f1b
            ,text = 'retreat'
            ,command = self.cmd_retreat
            ).pack(side=tk.LEFT)
        
        tk.Button(
             f1b
            ,text = 'advance'
            ,command = self.cmd_advance
            ).pack(side=tk.LEFT)


        return root

class GuiC(threading.Thread):
    
    def __init__(self, b_log=False):
        threading.Thread.__init__(self)
        self.start()
        self.myGui = BuildGuiC(b_log=b_log)

    def callback(self):
        self.root.quit()

    def run(self):
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.callback)
        self.root = self.myGui.build_gui_c(self.root)
        self.root.mainloop()



if __name__ == "__main__":

    g.init()
    
    gui = GuiC(b_log=True)