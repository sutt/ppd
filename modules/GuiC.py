import random, os, sys
import threading
import Tkinter as tk
import GlobalsC as g



class ConstructGui:

    ''' Stores context for Gui: object we have to reference later from outside thread '''

    def __init__(self, b_log=False):
        self.b_log = b_log
        self.play_button = None

    def cmd_retreat(self):
        g.switchRetreatFrame = True

    def cmd_advance(self):
        g.switchAdvanceFrame = True

    def cmd_rewind(self):
        g.switchRewind = True

    def cmd_fastforward(self):
        g.switchFastforward = True

    def cmd_play_sw(self):
        ''' play/pause '''
        if g.playOn:
            g.playOn = False
            self.play_button.configure(bg = 'gray')
        else:
            g.playOn = True
            self.play_button.configure(bg = '#000fff000')

    def cmd_writevid_sw(self):
        ''' turn on/off video frame write '''
        if g.writevidOn:
            g.writevidOn = False
            self.writevid_button.configure(bg = 'gray')
        else:
            g.writevidOn = True
            self.writevid_button.configure(bg = '#000fff000')

    def cmd_initWritevid_sw(self):
        g.initWriteVid = True

    def cmd_snapWriteVid_sw(self):
        g.switchWriteVid = True

    def set_int_frameDelay(self, boolVal):
        self.int_frameDelay.set(int(boolVal))

    def cmd_frameDelay(self):
        g.frameDelay = bool(self.int_frameDelay.get())

    def cmd_delaySecsSet(self):
        g.delaySecs = float(self.sv_delaySecs.get())

    def set_sv_writevidFn(self, strWriteVidFn):
        self.sv_writevidFn.set(str(strWriteVidFn))
    
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

    def set_sv_avgFrameFps(self, strAvgFps, strAvgFrameTime):
        if len(str(strAvgFps)) > 4:
            strAvgFps = str(strAvgFps)[:4]
        self.sv_avgFps.set(str(strAvgFps))
        if len(str(strAvgFrameTime)) > 6:
            strAvgFrameTime = str(strAvgFrameTime)[:6]
        self.sv_avgFrameTime.set(str(strAvgFrameTime))

    def set_sv_lags(self, lag0, lag1):
        if len(str(lag0)) > 6:
            lag0 = str(lag0)[:6]
        self.sv_lag0.set(str(lag0))
        if len(str(lag1)) > 6:
            lag1 = str(lag1)[:6]
        self.sv_lag1.set(str(lag1))

        
    def init_gui(self, **kwargs):
        ''' from main loop, set initial state of gui elements '''
        
        if kwargs.get('playOn', False):
            self.play_button.configure(bg = '#000fff000')

        if kwargs.get('frameDelay', None) is not None:
            self.set_int_frameDelay(kwargs.get('frameDelay', True))


    def build_gui(self, root):

        ''' attach the the gui boilerplate to the Tk() object passed in as root.
            if the element needs to be manipulated later, attach it to self as well.
        '''

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

        f1b2 = tk.Frame(root)
        f1b2.pack(side = tk.TOP)

        self.snapWriteVid_button = tk.Button(
             f1b2
            ,text = 'writeFrame'
            ,command = self.cmd_snapWriteVid_sw
            )
        self.snapWriteVid_button.pack()

        f1c = tk.Frame(root)
        f1c.pack(side = tk.TOP)
        
        tk.Button(
             f1c
            ,text = '<<'
            ,command = self.cmd_rewind
            ).pack(side=tk.LEFT)
        
        tk.Button(
             f1c
            ,text = '>>'
            ,command = self.cmd_fastforward
            ).pack(side=tk.LEFT)

        fwrite0 = tk.Frame(root)
        fwrite0.pack(side = tk.TOP)

        self.writevid_button = tk.Button(
                 fwrite0
                ,text = 'writevid'
                ,bg = 'gray'
                ,command = self.cmd_writevid_sw
                )
        self.writevid_button.pack(side=tk.LEFT)

        self.initWritevid_button = tk.Button(
                 fwrite0
                ,text = 'init output'
                ,bg = 'gray'
                ,command = self.cmd_initWritevid_sw
                )
        self.initWritevid_button.pack(side=tk.LEFT)
        
        fwrite1 = tk.Frame(root)
        fwrite1.pack(side = tk.TOP)

        self.sv_writevidFn = tk.StringVar()
        self.set_sv_writevidFn("n/a")
        
        self.dir_entry = tk.Entry(
                 fwrite1
                ,textvariable = self.sv_writevidFn
                ,width = 20
                ,bg = 'white'
                )
        self.dir_entry.pack(side=tk.LEFT)


        f1a5b = tk.Frame(root)
        f1a5b.pack(side = tk.TOP)

        tk.Label(f1a5b, text="True time:").pack(side=tk.LEFT)

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
        
        f0_1a = tk.Frame(root)
        f0_1a.pack(side = tk.TOP)

        tk.Label(f0_1a, text="delay secs:").pack(side=tk.LEFT)

        self.sv_delaySecs = tk.StringVar()
        self.sv_delaySecs.set("0.0")
        
        self.delaySecs_entry = tk.Entry(
                f0_1a
                ,textvariable = self.sv_delaySecs
                # ,command/on change?
                ,width = 7
                ,bg = 'white'
                )
        self.delaySecs_entry.pack(side=tk.LEFT)

        self.delaySecs_button = tk.Button(
                f0_1a
                ,text = 'set'
                ,bg = 'gray'
                ,command = self.cmd_delaySecsSet
                )
        self.delaySecs_button.pack(side=tk.LEFT)

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

        
        f0_4 = tk.Frame(root)
        f0_4.pack(side = tk.TOP)

        tk.Label(f0_4, text="avg FPS:").pack(side=tk.LEFT)

        self.sv_avgFps = tk.StringVar()
        self.sv_avgFps.set("-1")
        
        self.dir_entry = tk.Entry(
                f0_4
                ,textvariable = self.sv_avgFps
                ,width = 5
                ,bg = 'white'
                )
        self.dir_entry.pack(side=tk.LEFT)

        tk.Label(f0_4, text="  time:").pack(side=tk.LEFT)

        self.sv_avgFrameTime = tk.StringVar()
        self.sv_avgFrameTime.set("-1")
        
        self.dir_entry = tk.Entry(
                f0_4
                ,textvariable = self.sv_avgFrameTime
                ,width = 7
                ,bg = 'white'
                )
        self.dir_entry.pack(side=tk.LEFT)


        f0_5 = tk.Frame(root)
        f0_5.pack(side = tk.TOP)

        tk.Label(f0_5, text="lag -1:").pack(side=tk.LEFT)

        self.sv_lag0 = tk.StringVar()
        self.sv_lag0.set("-1")
        
        self.dir_entry = tk.Entry(
                f0_5
                ,textvariable = self.sv_lag0
                ,width = 7
                ,bg = 'white'
                )
        self.dir_entry.pack(side=tk.LEFT)

        tk.Label(f0_5, text=" lag +1:").pack(side=tk.LEFT)

        self.sv_lag1 = tk.StringVar()
        self.sv_lag1.set("-1")
        
        self.dir_entry = tk.Entry(
                f0_5
                ,textvariable = self.sv_lag1
                ,width = 7
                ,bg = 'white'
                )
        self.dir_entry.pack(side=tk.LEFT)


        return root

class GuiC(threading.Thread):

    ''' Dispatch a thread to do tk.mainloop()
            
            guiHeader is a reference to BuildGuiC class, it's 
            self holds methods and elements if attached. Reference 
            guiHeader to access methods outside thread.

            root is the tk-object and has tk elements attached; it 
            will perform mainloop
        
    '''
    
    def __init__(self, b_log=False):
        
        self.tk = tk.Tk()
        self.tk.protocol("WM_DELETE_WINDOW", self.callback)
        
        self.guiHeader = ConstructGui()
        self.tkElements = self.guiHeader.build_gui(self.tk)
        
        threading.Thread.__init__(self)
        
        self.start()
        
    def callback(self):
        self.root.quit()
        g.callExit = True
        

    def run(self):
        self.root = self.tkElements
        self.root.mainloop()


class GuiInterface:

    ''' 
        This acceses GuiConstructor and calls its method on data 
        input from an instance of this class outside this thread. 
    '''

    def __init__(self, guiObj):
        self.gui = guiObj


    def updateByVid( self
                    ,vidFn=""
                    ,frameTotal=0
                    ,cumTimeTotal=None
                    ,avgFrameFps=(None, None)
                    ):
        
        ''' call once per video '''        
        
        if self.gui is None: return

        self.gui.guiHeader.set_sv_vidFn(vidFn)
        
        self.gui.guiHeader.set_sv_frameN(str(frameTotal))

        if cumTimeTotal is not None:
            self.gui.guiHeader.set_sv_cumTotal(cumTimeTotal)

        if all([x is not None for x in avgFrameFps]):
            self.gui.guiHeader.set_sv_avgFrameFps(*avgFrameFps)


    def updateByFrame( self
                    ,frameCurrent=0
                    ,cumTimeCurrent=None
                    ,lagTuple=(None, None)
                    ):
        
        ''' call every time frame is changed.
            call after getFrame() for correct data on frameCounter'''        
        
        if self.gui is None: return

        self.gui.guiHeader.set_sv_frameI(str(frameCurrent))
        
        if cumTimeCurrent is not None:
            self.gui.guiHeader.set_sv_cumTime(str(cumTimeCurrent))

        if all([x is not None for x in lagTuple]):
            self.gui.guiHeader.set_sv_lags(*lagTuple)


    def update( self, **kwargs):
        
        ''' can be called from anywhere'''        
        
        if self.gui is None: return

        if kwargs.get('writevidFn', None) is not None:
            self.gui.guiHeader.set_sv_writevidFn(str(kwargs.get('writevidFn', "n/a")))
        

    def initGui(self, playOnVal, frameDelayVal):

        self.gui.guiHeader.init_gui( playOn = playOnVal
                                    ,frameDelay = frameDelayVal
                                    )
            



if __name__ == "__main__":

    import time

    g.init()
    g.playOn = True
    g.switchAdvanceFrame = False
    g.switchRetreatFrame = False
    g.frameDelay = True
    g.writevidOn = False
    g.initWriteVid = False

    gui = GuiC()

    gui.guiHeader.init_gui( playOn = g.playOn
                           ,frameDelay = g.frameDelay
                            )