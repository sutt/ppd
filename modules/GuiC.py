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

    def cmd_selectzoom(self):
        g.switchZoom = True

    def cmd_selectroimain(self):
        g.switchRoiMain = True

    def cmd_selectroizoom(self):
        g.switchRoiZoom = True

    def cmd_selectreset(self):
        g.switchSelectReset = True

    def cmd_windowTwo(self):
        g.windowTwo = bool(self.int_windowTwo.get())

    def cmd_windowThree(self):
        g.windowThree = bool(self.int_windowThree.get())

    def cmd_outputParams(self):
        g.switchOutputParams = True

    def cmd_alterParams(self):
        g.switchAlterParams = True

    def cmd_outputState(self):
        g.switchOutputState = True

    def cmd_deleteState(self):
        g.switchDeleteState = True

    def cmd_resetParams(self):
        g.switchResetParams = True

    def cmd_compression(self):
        g.compressionEnum = self.int_compression.get()

    def cmd_duplicates(self):
        g.duplicatesEnum = self.int_duplicates.get()

    def cmd_objenum(self):
        g.trackObjEnum = self.int_objenum.get()

    def cmd_scoretypeenum(self):
        g.trackTypeEnum = self.int_scoretypeenum.get()

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

    def cmd_snapWriteOveride_sw(self):
        g.switchOverideNote = True

    def cmd_snapWriteScoring_sw(self):
        g.switchWriteScoring = True

    def set_int_frameDelay(self, boolVal):
        self.int_frameDelay.set(int(boolVal))

    def cmd_frameDelay(self):
        g.frameDelay = bool(self.int_frameDelay.get())

    def cmd_annotateEnum(self):
        g.annotateObjEnum = bool(self.int_annotateEnum.get())

    def cmd_delaySecsSet(self):
        g.delaySecs = float(self.sv_delaySecs.get())

    def cmd_trackon(self):
        g.trackingOn = bool(self.int_trackon.get())

    def cmd_set_trackon(self, intTrackOn):
        self.int_trackon.set(int(intTrackOn))

    def cmd_sw_trackon(self):
        self.int_trackon.set(int(
                            not(bool(self.int_trackon.get()))
                            ))
        self.cmd_trackon()

    def set_int_compression(self, intCompressionEnum):
        self.int_compression.set(intCompressionEnum)
        self.cmd_compression()  #set global.compressionEnum

    def set_sv_writevidFn(self, strWriteVidFn):
        self.sv_writevidFn.set(str(strWriteVidFn))
    
    def set_sv_trackTimer(self, fTrackTimer):
        sOutput = str(fTrackTimer)
        if len(sOutput) >= 5:
            sOutput = sOutput[:5]
        if fTrackTimer == -1:
            sOutput = "-1"
        self.sv_trackTimer.set(sOutput)

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

    def cmd_keypress(self, e):
        if e.char == "p" or e.char == "q":
            self.cmd_play_sw()
        if e.char == "s":
            self.cmd_retreat()
        if e.char == "a":
            self.cmd_advance()
        if e.char == "f":
            self.cmd_snapWriteVid_sw()
        if e.char == "g":
            self.cmd_snapWriteScoring_sw()
        if e.char == "h":
            self.cmd_snapWriteOveride_sw()
        if e.char == "z":
            self.cmd_selectzoom()
        if e.char == "c":
            self.cmd_selectroimain()
        if e.char == "x":
            self.cmd_selectroizoom()
        if e.char == "w":
            self.cmd_writevid_sw()
        if e.char == "i":
            self.cmd_initWritevid_sw()
        if e.char == "t":
            self.cmd_sw_trackon()
        if e.char == "r":
            self.cmd_selectreset()
        if e.char == "o":
            self.cmd_outputState()
            

        
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
        
        root.bind("<Key>", self.cmd_keypress)

        f1a = tk.Frame(root)
        f1a.pack(side = tk.TOP)

        self.play_button = tk.Button(
                f1a
                ,text = 'Play <Q>'
                ,bg = 'gray'
                ,command = self.cmd_play_sw
                )
        self.play_button.pack()

        
        f1b = tk.Frame(root)
        f1b.pack(side = tk.TOP)
        
        tk.Button(
             f1b
            ,text = 'retreat <S>'
            ,command = self.cmd_retreat
            ).pack(side=tk.LEFT)
        
        tk.Button(
             f1b
            ,text = 'Advance'
            ,command = self.cmd_advance
            ).pack(side=tk.LEFT)

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

        fselect0 = tk.Frame(root)
        fselect0.pack(side = tk.TOP)
        
        tk.Button(
             fselect0
            ,text = 'select Zoom'
            ,command = self.cmd_selectzoom
            ).pack(side=tk.LEFT)
        
        fselect_label = tk.Frame(root)
        fselect_label.pack(side = tk.TOP)
        tk.Label(fselect_label, text="selection controls:").pack(side=tk.LEFT)
        
        fselect1 = tk.Frame(root)
        fselect1.pack(side = tk.TOP)

        tk.Button(
             fselect1
            ,text = 'roi main <C>'
            ,command = self.cmd_selectroimain
            ).pack(side=tk.LEFT)

        tk.Button(
             fselect1
            ,text = 'roi zoom <X>'
            ,command = self.cmd_selectroizoom
            ).pack(side=tk.LEFT)

        tk.Button(
             fselect1
            ,text = 'Reset'
            ,command = self.cmd_selectreset
            ).pack(side=tk.LEFT)

        fselect2 = tk.Frame(root)
        fselect2.pack(side = tk.TOP)

        self.int_objenum = tk.IntVar()
        self.int_objenum.set(0)
        
        tk.Label(fselect2, text="obj enum:").pack(side=tk.LEFT)
        tk.Radiobutton(
             fselect2
            ,text="0"
            ,variable=self.int_objenum
            ,value=0
            ,command=self.cmd_objenum
            ).pack(side=tk.LEFT)

        tk.Radiobutton(
             fselect2
            ,text="1"
            ,variable=self.int_objenum
            ,value=1
            ,command=self.cmd_objenum
            ).pack(side=tk.LEFT)

        tk.Radiobutton(
             fselect2
            ,text="2"
            ,variable=self.int_objenum
            ,value=2
            ,command=self.cmd_objenum
            ).pack(side=tk.LEFT)

        tk.Radiobutton(
             fselect2
            ,text="3"
            ,variable=self.int_objenum
            ,value=3
            ,command=self.cmd_objenum
            ).pack(side=tk.LEFT)

        fselect3 = tk.Frame(root)
        fselect3.pack(side = tk.TOP)

        self.int_scoretypeenum = tk.IntVar()
        self.int_scoretypeenum.set(0)
        
        tk.Label(fselect3, text="score type:").pack(side=tk.LEFT)
        tk.Radiobutton(
             fselect3
            ,text="circle"
            ,variable=self.int_scoretypeenum
            ,value=0
            ,command=self.cmd_scoretypeenum
            ).pack(side=tk.LEFT)

        tk.Radiobutton(
             fselect3
            ,text="ray"
            ,variable=self.int_scoretypeenum
            ,value=1
            ,command=self.cmd_scoretypeenum
            ).pack(side=tk.LEFT)



        f_output_label = tk.Frame(root)
        f_output_label.pack(side = tk.TOP)
        tk.Label(f_output_label, text="output controls:").pack(side=tk.LEFT)

        f1b2 = tk.Frame(root)
        f1b2.pack(side = tk.TOP)

        self.snapWriteVid_button = tk.Button(
             f1b2
            ,text = 'writeFrame'
            ,command = self.cmd_snapWriteVid_sw
            )
        self.snapWriteVid_button.pack(side=tk.LEFT)

        self.snapWriteScoring_button = tk.Button(
             f1b2
            ,text = 'writef+scorinG'
            ,command = self.cmd_snapWriteScoring_sw
            )
        self.snapWriteScoring_button.pack(side=tk.LEFT)

        f1b2_add = tk.Frame(root)
        f1b2_add.pack(side = tk.TOP)

        self.snapWriteOveride_button = tk.Button(
             f1b2_add
            ,text = 'writef+overide<H>'
            ,command = self.cmd_snapWriteOveride_sw
            )
        self.snapWriteOveride_button.pack(side=tk.LEFT)

        fwrite0 = tk.Frame(root)
        fwrite0.pack(side = tk.TOP)

        self.writevid_button = tk.Button(
                 fwrite0
                ,text = 'Writevid'
                ,bg = 'gray'
                ,command = self.cmd_writevid_sw
                )
        self.writevid_button.pack(side=tk.LEFT)

        self.int_duplicates = tk.IntVar()
        self.int_duplicates.set(g.duplicatesEnum)
        
        tk.Radiobutton(
             fwrite0
            ,text="no"
            ,variable=self.int_duplicates
            ,value=0
            ,command=self.cmd_duplicates
            ).pack(side=tk.LEFT)

        tk.Radiobutton(
             fwrite0
            ,text="allow dup's"
            ,variable=self.int_duplicates
            ,value=1
            ,command=self.cmd_duplicates
            ).pack(side=tk.LEFT)

        fwrite12 = tk.Frame(root)
        fwrite12.pack(side = tk.TOP)

        self.initWritevid_button = tk.Button(
                 fwrite12
                ,text = 'Init output'
                ,bg = 'gray'
                ,command = self.cmd_initWritevid_sw
                )
        self.initWritevid_button.pack(side=tk.LEFT)

        self.int_compression = tk.IntVar()
        self.int_compression.set(0)
        
        tk.Radiobutton(
             fwrite12
            ,text="h264"
            ,variable=self.int_compression
            ,value=0
            ,command=self.cmd_compression
            ).pack(side=tk.LEFT)

        tk.Radiobutton(
             fwrite12
            ,text="lossless"
            ,variable=self.int_compression
            ,value=1
            ,command=self.cmd_compression
            ).pack(side=tk.LEFT)
        
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

        fdisplaylabel = tk.Frame(root)
        fdisplaylabel.pack(side = tk.TOP)

        tk.Label(fdisplaylabel, text="display/run options:").pack(side=tk.LEFT)

        fdisplay1 = tk.Frame(root)
        fdisplay1.pack(side = tk.TOP)

        tk.Label(fdisplay1, text="zoom win:").pack(side=tk.LEFT)

        self.int_windowTwo = tk.IntVar()
        self.int_windowTwo.set(1)
        
        tk.Radiobutton(
             fdisplay1
            ,text="on"
            ,variable=self.int_windowTwo
            ,value=1
            ,command=self.cmd_windowTwo
            ).pack(side=tk.LEFT)

        tk.Radiobutton(
             fdisplay1
            ,text="off"
            ,variable=self.int_windowTwo
            ,value=0
            ,command=self.cmd_windowTwo
            ).pack(side=tk.LEFT)

        fdisplay2 = tk.Frame(root)
        fdisplay2.pack(side = tk.TOP)

        tk.Label(fdisplay2, text="diff win:").pack(side=tk.LEFT)

        self.int_windowThree = tk.IntVar()
        self.int_windowThree.set(0)
        
        tk.Radiobutton(
             fdisplay2
            ,text="on"
            ,variable=self.int_windowThree
            ,value=1
            ,command=self.cmd_windowThree
            ).pack(side=tk.LEFT)

        tk.Radiobutton(
             fdisplay2
            ,text="off"
            ,variable=self.int_windowThree
            ,value=0
            ,command=self.cmd_windowThree
            ).pack(side=tk.LEFT)


        f1a5b = tk.Frame(root)
        f1a5b.pack(side = tk.TOP)

        tk.Label(f1a5b, text="true time:").pack(side=tk.LEFT)

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

        f_annotate_enum = tk.Frame(root)
        f_annotate_enum.pack(side = tk.TOP)

        tk.Label(f_annotate_enum, text="annotate obj:").pack(side=tk.LEFT)

        self.int_annotateEnum = tk.IntVar()
        self.int_annotateEnum.set(0)
        
        tk.Radiobutton(
             f_annotate_enum
            ,text="on"
            ,variable=self.int_annotateEnum
            ,value=1
            ,command=self.cmd_annotateEnum
            ).pack(side=tk.LEFT)

        tk.Radiobutton(
             f_annotate_enum
            ,text="off"
            ,variable=self.int_annotateEnum
            ,value=0
            ,command=self.cmd_annotateEnum
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

        ftrack1 = tk.Frame(root)
        ftrack1.pack(side = tk.TOP)

        tk.Label(ftrack1, text="Track:").pack(side=tk.LEFT)

        self.int_trackon = tk.IntVar()
        self.int_trackon.set(0)
        
        tk.Radiobutton(
             ftrack1
            ,text="on"
            ,variable=self.int_trackon
            ,value=1
            ,command=self.cmd_trackon
            ).pack(side=tk.LEFT)

        tk.Radiobutton(
             ftrack1
            ,text="off"
            ,variable=self.int_trackon
            ,value=0
            ,command=self.cmd_trackon
            ).pack(side=tk.LEFT)

        ftrack2 = tk.Frame(root)
        ftrack2.pack(side = tk.TOP)

        tk.Label(ftrack2, text="track timer:").pack(side=tk.LEFT)

        self.sv_trackTimer = tk.StringVar()
        self.set_sv_trackTimer("n/a")
        
        self.dir_entry = tk.Entry(
                ftrack2
                ,textvariable = self.sv_trackTimer
                ,width = 6
                ,bg = 'white'
                )
        self.dir_entry.pack(side=tk.LEFT)

        ftrack3 = tk.Frame(root)
        ftrack3.pack(side = tk.TOP)

        tk.Label(ftrack3, text="track params:").pack(side=tk.LEFT)

        tk.Button(
             ftrack3
            ,text = 'output'
            ,command = self.cmd_outputParams
            ).pack(side=tk.LEFT)

        tk.Button(
             ftrack3
            ,text = 'alter'
            ,command = self.cmd_alterParams
            ).pack(side=tk.LEFT)

        tk.Button(
             ftrack3
            ,text = 'reset'
            ,command = self.cmd_resetParams
            ).pack(side=tk.LEFT)

        fstate1 = tk.Frame(root)
        fstate1.pack(side = tk.TOP)

        tk.Label(fstate1, text="output state:").pack(side=tk.LEFT)

        tk.Button(
             fstate1
            ,text = 'Output'
            ,command = self.cmd_outputState
            ).pack(side=tk.LEFT)

        tk.Button(
             fstate1
            ,text = 'delete'
            ,command = self.cmd_deleteState
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

        frame_keypress = tk.Frame(root)

        tk.Radiobutton(
             frame_keypress
            ,text="on"
            ,variable=self.int_windowTwo
            ,value=1
            ,command=self.cmd_windowTwo
            ).pack(side=tk.LEFT)

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
                    ,compressionType=0
                    ,frameTotal=0
                    ,cumTimeTotal=None
                    ,avgFrameFps=(None, None)
                    ,trackingOn=None
                    ):
        
        ''' call once per video '''        
        
        if self.gui is None: return

        self.gui.guiHeader.set_sv_vidFn(vidFn)
        
        self.gui.guiHeader.set_int_compression(compressionType)

        self.gui.guiHeader.set_sv_frameN(str(frameTotal))

        if cumTimeTotal is not None:
            self.gui.guiHeader.set_sv_cumTotal(cumTimeTotal)

        if all([x is not None for x in avgFrameFps]):
            self.gui.guiHeader.set_sv_avgFrameFps(*avgFrameFps)

        if trackingOn is not None:
            self.gui.guiHeader.cmd_set_trackon(int(trackingOn))


    def updateByFrame( self
                    ,frameCurrent=0
                    ,cumTimeCurrent=None
                    ,lagTuple=(None, None)
                    ,trackTimer=None
                    ):
        
        ''' call every time frame is changed.
            call after getFrame() for correct data on frameCounter'''        
        
        if self.gui is None: return

        self.gui.guiHeader.set_sv_frameI(str(frameCurrent))
        
        if cumTimeCurrent is not None:
            self.gui.guiHeader.set_sv_cumTime(str(cumTimeCurrent))

        if all([x is not None for x in lagTuple]):
            self.gui.guiHeader.set_sv_lags(*lagTuple)

        if trackTimer is not None:
            self.gui.guiHeader.set_sv_trackTimer(trackTimer)


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