import random, os, sys
import threading
import Tkinter as tk
import GlobalsC as g


class GuiData:

    def __init__(self):
        self.sv_vidFn = None
        self.sv_frameI = None
        self.sv_cumTime = None
        self.play_button = None


class BuildGuiC:

    def __init__(self, b_log=False):
        self.b_log = b_log
        self.play_button = None

    def cmd_retreat(self):
        g.switchRetreatFrame = True

    def cmd_advance(self):
        g.switchAdvanceFrame = True

    def cmd_play_sw(self):
        ''' play/pause '''
        if g.playOn:
            g.playOn = False
            self.play_button.configure(bg = 'gray')
        else:
            g.playOn = True
            self.play_button.configure(bg = '#000fff000')

    def set_sv_vidFn(self, strVidFn):
        self.sv_vidFn.set(str(strVidFn))

    def set_sv_frameI(self, strFrameI):
        self.sv_frameI.set(str(strFrameI))

    def set_sv_cumTime(self, strCumTime):
        self.sv_cumTime.set(str(strCumTime))
        
        

    def build_gui_c(self, root):

        f1a = tk.Frame(root)
        f1a.pack(side = tk.TOP)

        self.play_button = tk.Button(
                f1a
                ,text = 'play toggle'
                ,bg = 'gray'
                ,command = self.cmd_play_sw
                )
        self.play_button.pack()

        
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

        f0_1 = tk.Frame(root)
        f0_1.pack(side = tk.TOP)

        tk.Label(f0_1, text="file:").pack(side=tk.LEFT)

        self.sv_vidFn = tk.StringVar()
        self.set_sv_vidFn("n/a")
        
        self.dir_entry = tk.Entry(
                f0_1
                ,textvariable = self.sv_vidFn
                ,width = 15
                ,bg = 'white'
                )
        self.dir_entry.pack(side=tk.LEFT)

        f0_2 = tk.Frame(root)
        f0_2.pack(side = tk.TOP)

        tk.Label(f0_2, text="frame_i:").pack(side=tk.LEFT)

        self.sv_frameI = tk.StringVar()
        self.set_sv_frameI(-1)
        
        self.dir_entry = tk.Entry(
                f0_2
                ,textvariable = self.sv_frameI
                ,width = 15
                ,bg = 'white'
                )
        self.dir_entry.pack(side=tk.LEFT)

        f0_3 = tk.Frame(root)
        f0_3.pack(side = tk.TOP)

        tk.Label(f0_3, text="cum time:").pack(side=tk.LEFT)

        self.sv_cumTime = tk.StringVar()
        self.set_sv_cumTime("-1")
        
        self.dir_entry = tk.Entry(
                f0_3
                ,textvariable = self.sv_cumTime
                ,width = 15
                ,bg = 'white'
                )
        self.dir_entry.pack(side=tk.LEFT)


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