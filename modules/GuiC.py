import random, os, sys
import threading
import Tkinter as tk
import GlobalsC as g


class GuiData:

    def __init__(self):
        self.sv_vidFn = None
        self.sv_frameI = None
        self.sv_frameN = None
        self.sv_cumTime = None
        self.sv_cumTotal = None
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

    def set_int_frameDelay(self, boolVal):
        self.int_frameDelay.set(int(boolVal))

    def cmd_frameDelay(self):
        g.frameDelay = bool(self.int_frameDelay.get())

    def set_sv_vidFn(self, strVidFn):
        self.sv_vidFn.set(str(strVidFn))

    def set_sv_frameI(self, strFrameI):
        self.sv_frameI.set(str(strFrameI))

    def set_sv_frameN(self, strFrameN):
        self.sv_frameN.set(str(strFrameN))

    def set_sv_cumTime(self, strCumTime):
        self.sv_cumTime.set(str(strCumTime))

    def set_sv_cumTotal(self, strCumTotal):
        if len(str(strCumTotal)) > 4:
            strCumTotal = str(strCumTotal)[:4]
        self.sv_cumTotal.set(str(strCumTotal))
        
    def initGui(self, **kwargs):
        ''' from main loop, set initial state of gui elements '''
        
        if kwargs.get('playOn', False):
            self.play_button.configure(bg = '#000fff000')

        if kwargs.get('frameDelay', None) is not None:
            self.set_int_frameDelay(kwargs.get('frameDelay', True))


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

        f1a5b = tk.Frame(root)
        f1a5b.pack(side = tk.TOP)

        tk.Label(f1a5b, text="Frame Delay:").pack(side=tk.LEFT)

        self.int_frameDelay = tk.IntVar()
        self.int_frameDelay.set(1)
        
        tk.Radiobutton(
             f1a5b
            ,text="on"
            ,variable=self.int_frameDelay
            ,value=1
            ,command=self.cmd_frameDelay
            ).pack(side=tk.LEFT)

        tk.Radiobutton(
             f1a5b
            ,text="off"
            ,variable=self.int_frameDelay
            ,value=0
            ,command=self.cmd_frameDelay
            ).pack(side=tk.LEFT)

        f0_2 = tk.Frame(root)
        f0_2.pack(side = tk.TOP)

        tk.Label(f0_2, text="frame_i:").pack(side=tk.LEFT)

        self.sv_frameI = tk.StringVar()
        self.set_sv_frameI(-1)
        
        self.dir_entry = tk.Entry(
                f0_2
                ,textvariable = self.sv_frameI
                ,width = 7
                ,bg = 'white'
                )
        self.dir_entry.pack(side=tk.LEFT)

        tk.Label(f0_2, text="  of:").pack(side=tk.LEFT)

        self.sv_frameN = tk.StringVar()
        self.set_sv_frameN(-1)
        
        self.dir_entry = tk.Entry(
                f0_2
                ,textvariable = self.sv_frameN
                ,width = 4
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
                ,width = 7
                ,bg = 'white'
                )
        self.dir_entry.pack(side=tk.LEFT)

        tk.Label(f0_3, text="  of:").pack(side=tk.LEFT)

        self.sv_cumTotal = tk.StringVar()
        self.set_sv_cumTotal("-1")
        
        self.dir_entry = tk.Entry(
                f0_3
                ,textvariable = self.sv_cumTotal
                ,width = 4
                ,bg = 'white'
                )
        self.dir_entry.pack(side=tk.LEFT)


        return root

class GuiC(threading.Thread):
    
    def __init__(self, b_log=False):
        
        self.tk = tk.Tk()
        self.tk.protocol("WM_DELETE_WINDOW", self.callback)
        
        self.myGui = BuildGuiC(b_log=b_log)
        self.myGuiCode = self.myGui.build_gui_c(self.tk)
        
        threading.Thread.__init__(self)
        
        self.start()
        
    def callback(self):
        self.root.quit()

    def run(self):
        self.root = self.myGuiCode
        self.root.mainloop()



if __name__ == "__main__":

    import time

    g.init()
    g.playOn = True
    g.switchAdvanceFrame = False
    g.switchRetreatFrame = False
    g.frameDelay = True
    
    gui = GuiC(b_log=True)

    gui.myGui.initGui(playOn = g.playOn
                     ,frameDelay = g.frameDelay
                     )