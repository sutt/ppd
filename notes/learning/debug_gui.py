import cv2
import threading
import Tkinter as tk

'''
This is an attempt to run debug (with vscode) and pause and restart w/o problems an
app using both tkinter and cv2. Presently, that can't be acheived in guiview.

Hacks to fix it?
[x] try to step gently in guiview
    no: it doesn't even pause/continue and work; no chance to try to step
[ ] set breakpoint in gui class, not mainloop

Try to isolate the problem:
[ ] tkinter
    [ ] non threaded tk?
    [ ] that message when you debug? using interactive 'Agg' backend?
[ ] threading
[ ] cv2
[ ] time.sleep (e.g. in frameDelay())
[ ] globals

[ ] maybe the problem is how you set breakpoints? debuggin methodology in general?

[ ] use __debug__? This is weird, doesn't do what you think

[x] try with a more basic thread? is the problem ptvsd?

    This seems promising, this works.
    Is this because start is called in main()?
        no, that didsn't translate to basic...

    [ ] set debugger to something else?
    https://code.visualstudio.com/docs/python/debugging
    
    ptvsd:
        https://github.com/Microsoft/ptvsd/ (explains cmdline opts)
        https://pypi.org/project/ptvsd/ (pip install ptvsd)
    
        open issues with "thread":
        https://github.com/Microsoft/ptvsd/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aopen+thread

[ ] could be a problem with using integratedTerminal = bash  (not cmd)

[ ] inline GuiConstructor methods into GuiC 

[ ] could be in the debug options?
    [ ] execute ptsvd from cmd line
        
        $ cd "c:\Users\wsutt\Desktop\files\ppd\ppd\notes\learning" ; env "PYTHONIOENCODING=UTF-8" "PY
            THONUNBUFFERED=1" "PYTHONPATH=c:\Users\wsutt\.vscode\extensions\ms-python.python-2018.8.0\pyt
            honFiles\experimental\ptvsd" python -m ptvsd --host localhost --port 62570 "c:\Users\wsutt\De
            sktop\files\ppd\ppd\notes\learning\debug_gui.py" --file data/test/guiview/write_time/output4.
            avi

    >env "PYTHONPATH=c:\Users\wsutt\.vscode\extensions\ms-python.python-2018.8.0\pythonFiles\experimental\ptvsd"; python -m ptvsd --host localhost --port 62570 "c:\Users\wsutt\Desktop\files\ppd\ppd\notes\learning\debug_gui.py" --file data/test/guiview/write_time/output4.avi
    >python -m ptvsd --host localhost --port 62570 "c:\Users\wsutt\Desktop\files\ppd\ppd\notes\learning\debug_gui.py" --file data/test/guiview/write_time/output4.avi

    env "PYTHONIOENCODING=UTF-8" "PYTHONUNBUFFERED=1" "PYTHONPATH=c:\Users\wsutt\.vscode\extensions\ms-python.python-2018.8.0\pythonFiles\experimental\ptvsd" python -m ptvsd --host localhost --port 63480 "c:\Users\wsutt\Desktop\files\ppd\ppd\notes\learning\debug_gui.py" --file data/test/guiview/write_time/output4.avi --nodelay

[ ] can you reproduce the hold down spacebar crash bug?
    [ ] can you eliminate this by eliminating globals?
    [ ] Try to build a better gui -> mainloop data transfer method

Notes:

    already encountering the problem after several pause/continue cycles
    in basic. Fans spinning on allegedely running tk is set to continue but
    never regains focus.

        it seems like you can do unlimited pause/continue as long as you
        don't start stepping thru rapidly

    biig clue: main while loop slows down significantly after first pause/continue:
        30x slow down
        this also happens when there's a breakpoint in the mainthread:while-loop

    When pausing basic():
        only mainthread is paused, gui-thread stays running

    thrashing f10 appears to be the things that breaks basic(); can run
    indefinetly pause/continue/Step as long as you step slowly
    (but is this only with print off?)

    Debugging matplotlib import get this message:
        Backend TkAgg is interactive backend. Turning interactive mode on.

    Closest Stackoverflow question:
    https://stackoverflow.com/questions/35819769/python-method-strangely-on-pause-until-tkinter-root-is-closed

    From previous notes:
        also note, this version use *G*TkAgg not TkAgg 
        matplotlib.use('GTKAgg')

        http://www.pyimagesearch.com/2015/08/24/resolved-matplotlib-figures-not-showing-up-or-displaying/

			>>> import matplotlib
			>>> matplotlib.get_backend()
			'TkAgg'

            sudo apt-get install tcl-dev tk-dev python-tk python3-tk

    >>> Tkinter.__version__
    '$Revision: 81008 $'

    Since we're importing with a captial T we're pre-version-3 according to https://wiki.python.org/moin/TkInter

    Could be a problem with the vscode python tools supplied debugger:
    c:\Users\wsutt\.vscode\extensions\ms-python.python-2018.8.0\pythonFiles\experimental\ptvsd


'''

global bExit
bExit = False

class ConstructGui:

    ''' Stores context for Gui: object we have to reference later from outside thread '''

    def __init__(self, b_log=False):
        self.i = 0
        self.b_log = b_log
        self.play_button = None
        
    def cmd_writevid_sw(self):
        self.i += 1
        print 'push!'

    #Note: not any method holder

    def build_gui(self, root):

        ''' attach the the gui boilerplate to the Tk() object passed in as root.
            if the element needs to be manipulated later, attach it to self as well.
        '''

        
        f0_5 = tk.Frame(root)
        f0_5.pack(side = tk.TOP)
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

        self.writevid_button = tk.Button(
                 f0_5
                ,text = 'writevid'
                ,bg = 'gray'
                ,command = self.cmd_writevid_sw
                )
        self.writevid_button.pack(side=tk.LEFT)


        return root

class GuiC(threading.Thread):

    
    def __init__(self, b_log=False):
        
        self.tk = tk.Tk()
        self.bExit = bExit
        # self.tk.protocol("WM_DELETE_WINDOW", self.callback)  
        self.guiHeader = ConstructGui()
        self.tkElements = self.guiHeader.build_gui(self.tk)
        # self.tkElements.
        threading.Thread.__init__(self)
        self.i = 0
        # self.start()            #Call this outside?
        
    # def callback(self):
    #     #better call back?
    #     self.root.quit()
    #     # g.callExit = True
    #     #eliminate this whole thing?
        

    def run(self):
        self.root = self.tkElements
        self.i += 1
        # self.root.
        self.root.mainloop()
        # self.tkElements.mainloop()

def GuiD():

    _tk = tk.Tk()

    f0_5 = tk.Frame(_tk)
    f0_5.pack(side = tk.TOP)
    tk.Label(f0_5, text=" lag +1:").pack(side=tk.LEFT)

    sv_lag1 = tk.StringVar()
    sv_lag1.set("-1")
    
    dir_entry = tk.Entry(
            f0_5
            ,textvariable = sv_lag1
            ,width = 7
            ,bg = 'white'
            )
    dir_entry.pack(side=tk.LEFT)

    _tk.mainloop()




def basic():

    ''' Run a tkinter in mainloop, while prinitng to console '''

    import time

    gui = GuiC()
    gui.start()

    mod = 10**7
    
    if __debug__:
        # print 'debugging!'
        mod = 10**6

    i=0
    t0 = time.time()
    while(True):
        i += 1
        if i % mod == 0:
            print str(time.time() - t0)[:4]
            t0 = time.time()

def basic_thread():

    import time
    
    mod = 10**7
    
    if bool(__debug__):
        print 'debugging!'
        mod = 10**6
    
    def myfunc():
        j = 0
        while(True):
            j += 1
            if j % mod == 0:
                # j = 0
                print j
            if j > 10**7:
                break

    t = threading.Thread(target=myfunc)
    t.start()

    i=0
    t0 = time.time()
    while(True):
        i += 1
        if i % mod == 0:
            print str(time.time() - t0)[:4]
            t0 = time.time()


def new_thread():

    import time
    
    mod = 10**7
    
    if bool(__debug__):
        print 'debugging!'
        mod = 10**6
    
    def myfunc():
        j = 0
        while(True):
            j += 1
            if j % mod == 0:
                # j = 0
                print j
            if j > 10**7:
                break

    t = threading.Thread(target=GuiD)
    t.start()

    i=0
    t0 = time.time()
    while(True):
        i += 1
        if i % mod == 0:
            print str(time.time() - t0)[:4]
            t0 = time.time()



if __name__ == "__main__":
    basic()
    # basic_thread()
    # new_thread()