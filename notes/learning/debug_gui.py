import cv2
import threading
import Tkinter as tk

'''
This is an attempt to run debug (with vscode) and pause and restart w/o problems an
app using both tkinter and cv2. Presently, that can't be acheived in guiview.

Hacks to fix it?
[ ] try to step gently in guiview

Try to isolate the problem:
[ ] tkinter
    [ ] non threaded tk?
    [ ] that message when you debug? using interactive 'Agg' backend?
[ ] threading
[ ] cv2
[ ] time.sleep (e.g. in frameDelay())
[ ] globals

[ ] maybe the problem is how you set breakpoints? debuggin methodology in general?

[ ] use __debug__?

[ ] inline GuiConstructor methods into GuiC 

[ ] could be in the debug options?
    [ ] execute ptsvd from cmd line
        
        $ cd "c:\Users\wsutt\Desktop\files\ppd\ppd\notes\learning" ; env "PYTHONIOENCODING=UTF-8" "PY
            THONUNBUFFERED=1" "PYTHONPATH=c:\Users\wsutt\.vscode\extensions\ms-python.python-2018.8.0\pyt
            honFiles\experimental\ptvsd" python -m ptvsd --host localhost --port 62570 "c:\Users\wsutt\De
            sktop\files\ppd\ppd\notes\learning\debug_gui.py" --file data/test/guiview/write_time/output4.
            avi

    python -m ptvsd --host localhost --port 62570 "c:\Users\wsutt\Desktop\files\ppd\ppd\notes\learning\debug_gui.py" --file data/test/guiview/write_time/output4.avi

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


'''

class ConstructGui:

    ''' Stores context for Gui: object we have to reference later from outside thread '''

    def __init__(self, b_log=False):
        self.b_log = b_log
        self.play_button = None

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


        return root

class GuiC(threading.Thread):

    
    def __init__(self, b_log=False):
        
        self.tk = tk.Tk()
        # self.tk.protocol("WM_DELETE_WINDOW", self.callback)  
        self.guiHeader = ConstructGui()
        self.tkElements = self.guiHeader.build_gui(self.tk)
        threading.Thread.__init__(self)
        self.start()            #Call this outside?
        
    def callback(self):
        #better call back?
        self.root.quit()
        # g.callExit = True
        

    def run(self):
        self.root = self.tkElements
        self.root.mainloop()
        # self.tkElements.mainloop()


def basic():

    ''' Run a tkinter in mainloop, while prinitng to console '''

    import time

    gui = GuiC()

    mod = 10**7
    
    if __debug__:
        print 'debugging!'
        mod = 10**6

    i=0
    t0 = time.time()
    while(True):
        i += 1
        if i % mod == 0:
            print str(time.time() - t0)[:4]
            t0 = time.time()

if __name__ == "__main__":
    basic()