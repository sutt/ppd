import os, sys, copy
import subprocess
import time

sys.path.append("../")
from modules.ControlFlow import FrameFactory
from modules.ControlFlow import TimeFactory
from modules.ControlFlow import DirectoryFactory
import modules.GlobalsC as g

'''
Architecture:
>pytest guiview_test.py -vv
    pytest collects test_functions from guiview_test.py
    test functions are instatiation of GuiviewStaging and a call to 
        the respective test_method
    the test_method calls a subprocess on guiview with supporting args
    the test method uses
    guiview imports mocks and stubs at very stages in script execution:
        - stubs act like the gui, setting variables to change to make the 
        program function.
        - mocks let us do asserts on the state of the program at various points
          if an assert fails it gets written with the proc to stderr, which is being
          piped to 
    as test_method closes it checks the stderr it has read for errors
    if there's any errors there, it throws an error and the test kicksout
    also you can check the program returncode
    also you can check the timeout wrapped around the function

Todo:

    [x] run a subproc
    [ ] timeout
    [ ] timeout wrapper
    [ ] modify test video files to be shorter

    Tests:
    [x] basic_dir
    [x] basic_file
    [x] a true positive: find an exception err 
    [x] file not found
    [x] a video that cant be read within a dir of valid vids
    [ ] true time vs nodelay
    [x] firstN
    [ ] advance + retreat frame
    [ ] no logs
    [ ] frame lag on delay vid



Primer: How to Add a Test

    Make a new method in GuiviewStagingClass:
        
        figure out the params to call the script with.

    Add any particular mock and stub methods you need. (up to 8 possible):
        
        name them: <test-name>_<mock-position> 
            e.g.   basic_frame(), load_file_err_vid()

        there are 3 positions:
            vid:   get's called before a video opens/after it closes
            frame: get's called once for each frame loop
            exit:  the last line of the program

        also
            data:  what gets loaded into the mock or stub class on init; e.g. counters

        add those functions to the vidByStr, frameByStr, exitByStr lookup functions

            if you don't create custom function for these, they will

    Finally, add a call to the GuiviewStagingClass.new_test_method() in a function at 
        the end with the word 'test_' in it; for collection 
    
    One trick to make it easier: by calling guiview directly with --test <test-name>
    along with all the other flags you want you can see how the test is working, print
    to stdout, or even run debug with aforementioned flags.

'''

#proc.stderr.readline() looks for this
STDERR_EXIT_MSG = "script done"     


class GuiviewStagingClass:

    '''
        This calls a subprocess with specified cmd line flags and then watches
        the stderr from the subprocess from Exceptions raised from within
        the subprocess, probably from a Assertion Error in a GuiviewMock method.
    '''

    def __init__(self):
        pass

    #Helper Functions ------------------------------------------------

    @staticmethod
    def watchProcess(proc, b_poll=True):

        stderrLog = []

        #pre-check with poll() in caase program crashes right away
        
        while(True):

            lineStderr = proc.stderr.readline().strip()
            
            if lineStderr != "":

                if lineStderr.find(STDERR_EXIT_MSG) > -1:
                    break

                stderrLog.append(lineStderr)
                #or, raise immediately

            if b_poll:
                if proc.poll() is not None:
                    # p.returncode
                    break
        
        return stderrLog


    @staticmethod
    def launchProcess(args):
        proc =  subprocess.Popen(args
                                ,stderr = subprocess.PIPE
                                ,stdout = subprocess.PIPE
                                ,cwd = "../"
                                )
        #do a poll here to verify program has launched
        return proc

    @staticmethod
    def parseErrors(list_str_msg):        
        numErrors = 0
        for s in list_str_msg:
            if 'AssertionError' in s:
                numErrors += 1
        return (numErrors > 0)


    @staticmethod
    def argsFromCmd(strCmd):
        strCmd = strCmd.replace("\t", "")
        strCmd = strCmd.replace("\n", " ")
        args = strCmd.split(" ")
        args = filter(lambda s: s != "", args)
        return args
    
    #Test Setups ----------------------------------------------------------------
    
    def basic(self):
        ''' verify that multi vids run in a --dir run.
            verify all videos in specified directory are played at least 5 frames
                within 20 seconds.
        '''

        cmd = '''python guiview.py --test basic --nogui --noshow 
                                    --dir data/test/guiview/basic/
                                    --firstN 10'''

        args = self.argsFromCmd(cmd)
        
        p = self.launchProcess(args)
        
        msg = self.watchProcess(p)

        bErrors = self.parseErrors(msg)

        if bErrors:
            print "\n".join(msg)
            raise Exception("TEST FAIL: basic")

    def basic_file(self):
        ''' verify that a --file run opens up a frame.
            verify that frame is frame=0, and remains there b/c open_on_pause.
        '''

        cmd = '''python guiview.py --test basic_file --nogui --noshow 
                                    --file data/test/guiview/basic/output4.avi'''

        args = self.argsFromCmd(cmd)
        
        p = self.launchProcess(args)
        
        msg = self.watchProcess(p)

        bErrors = self.parseErrors(msg)

        if bErrors:
            print "\n".join(msg)
            raise Exception("TEST FAIL: basic_file")

    def true_positive(self):
        ''' verify that an assert within the subprocess gets caught here.
        '''

        cmd = '''python guiview.py --test true_positive --nogui --noshow 
                                    --file data/test/guiview/basic/output4.avi'''

        args = self.argsFromCmd(cmd)
        
        p = self.launchProcess(args)
        
        msg = self.watchProcess(p)

        bErrors = self.parseErrors(msg)

        if not(bErrors):
            print "\n".join(msg)
            raise Exception("TEST FAIL: true_positive (should have bErrors)")


    def file_err(self):
        ''' open an invalid --file, make sure it does exit but does so gracefully'''
        
        cmd = '''python guiview.py --test file_err --nogui --noshow 
                                    --file data/test/guiview/basic/notafn.avi'''

        args = self.argsFromCmd(cmd)
        
        p = self.launchProcess(args)
        
        msg = self.watchProcess(p)

        bErrors = self.parseErrors(msg)

        if bErrors:
            print "\n".join(msg)
            raise Exception("TEST FAIL: file err")

    def file_err_dir(self):
        ''' have an invalid .avi file (output6.avi) in a dir with other valid .avi files.
            verify that the valids run thru multiple times on --dir
        '''

        cmd = '''python guiview.py --test file_err_dir --nogui --noshow 
                                --dir data/test/guiview/file_err_dir/
                                --firstN 10'''

        args = self.argsFromCmd(cmd)
        
        p = self.launchProcess(args)
        
        msg = self.watchProcess(p)

        bErrors = self.parseErrors(msg)

        if bErrors:
            print "\n".join(msg)
            raise Exception("TEST FAIL: fil_err_dir")


    


class GuiviewMock:

    '''
        Mock: this is used to run asserts on different classes at particular points
              within the guiview program.
    '''

    def __init__(self, strTest):
        self.mockCounter = 0
        self.dataByStr(strTest)

    #Boilerplate ------------------------------
    
    def dataByStr(self, strTest):
        ''' put data for needed for this particular test into self'''

        if strTest == "basic":
            self.basic_data()
        elif strTest == "file_err_dir":
            self.file_err_dir_data()
        else:
            self.dummy()

    def frameByStr(self, strTest):
        
        if strTest == "basic":
            return self.basic_frame
        elif strTest == "basic_file":
            return self.basic_file_frame
        elif strTest == "true_positive":
            return self.true_positive_frame
        elif strTest =="file_err":
            return self.file_err_frame
        elif strTest =="file_err_dir":
            return self.file_err_dir_frame
        else:
            return self.dummy

    def vidByStr(self, strTest):

        if strTest == "basic":
            return self.dummy
        elif strTest == "file_err":
            return self.file_err_vid
        else:
            return self.dummy

    def exitByStr(self, strTest):
        
        if strTest == "basic":
             return self.basic_exit
        elif strTest == "file_err_dir":
            return self.file_err_dir_exit
        else:
            return self.dummy

    def dummy(self, *args):
        pass

    
    #Mock Test: basic -------------------------------------

    def basic_data(self):
        self.requestedVids = ["output4.avi", "output5.avi", 
                              "output6.avi", "output7.avi"]

    def basic_frame( self
                    ,_frameFactory
                    ,_timeFactory
                    ,_directoryFactory
                    ):

        if _frameFactory.getFrameCounter() == 5:
        
            vidFn = _directoryFactory.vidFn()

            if vidFn in self.requestedVids:

                self.requestedVids.pop(self.requestedVids.index(vidFn))

    def basic_exit(self):
        
        #All videos have been popped and thus played
        assert len(self.requestedVids) == 0

    def basic_file_frame( self, 
                            _frameFactory
                            ,_timeFactory
                            ,_directoryFactory
                            ):
        
        #this opens on pause, frame counter should start here,
        #and continue to remain here.
        assert _frameFactory.getFrameCounter() ==  0
            
    def true_positive_frame( self, 
                            _frameFactory
                            ,_timeFactory
                            ,_directoryFactory
                            ):
        
        #deliberately trigger an assert error here
        assert _frameFactory.getFrameCounter() ==  99

    #Mock Test: file_err  -------------------------------------

    def file_err_frame(self, *args):
        self.mockCounter += 1
    
    def file_err_vid(   self
                        ,_frameFactory
                        ,_timeFactory
                        ,_directoryFactory
                        ):

        #check that program flow was as expected: 1 pass through frameloop
        print self.mockCounter
        assert self.mockCounter == 0

        #check that exit conditions are met
        assert _frameFactory.getFailedLoad() == True
        assert _timeFactory.checkExit(_frameFactory.getFailedLoad()) == True


    #Mock Test: file_err_dir  -------------------------------------

    def file_err_dir_data(self):
        self.requestedVids = ["output4.avi", "output5.avi", 
                              "output6.avi"]
        
        #two copies of each
        self.requestedVids += copy.copy(self.requestedVids)

    def file_err_dir_frame( self
                            ,_frameFactory
                            ,_timeFactory
                            ,_directoryFactory
                            ):

        if _frameFactory.getFrameCounter() == 5:
        
            vidFn = _directoryFactory.vidFn()

            if vidFn in self.requestedVids:

                self.requestedVids.pop(self.requestedVids.index(vidFn))

        self.stubCounter += 1


    def file_err_dir_exit(self):
        
        #Verify all videos have been popped and thus played twice in dir, 
        # except for the invalid dir, thus validating it runs over problem files
        assert len(self.requestedVids) == 2

        assert self.requestedVids[0] == "output6.avi"
        


class GuiviewStub:

    ''' Stub:   this is used to force app-state modification needed 
                to drive app, similiar to how a user would modify the gui.
            
            (since this module imports globals; those can be read/modified here,
             without even passing in a refernce from the main program.)

            note: all <test-name>_exit functions, including dummy_exit 
                  needs to raise a specifc exception-message to allow 
                  watchProcess to see that the subprocess is terminating.
    '''

    def __init__(self, strTest):
        self.stubCounter = 0
        self.dataByStr(strTest)

    #Boilerplate ---------------------------------
    
    def dataByStr(self, strTest):
        ''' put data for needed for this particular test into self '''

        if strTest == "basic":
            self.basic_data()
        # elif strTest
        else:
            self.dummy()

    def frameByStr(self, strTest):
        
        if strTest == "basic_file":
            return self.basic_file_frame
        elif strTest == "file_err_dir":
            return self.file_err_dir_frame
        else:
            return self.dummy

    def vidByStr(self, strTest):

        if strTest == "basic":
            return self.basic_vid
        # elif strTest
        else:
            return self.dummy

    def exitByStr(self, strTest):
        
        if strTest == "basic":
             return self.dummy_exit
        else:
            return self.dummy_exit

    def dummy(self, *args):
        pass

    def dummy_exit(self, *args):
        pass
        raise Exception(STDERR_EXIT_MSG)

    #Test: basic ----------------------------------

    def basic_data(self):
        self.t0 = time.time()

    def basic_vid(self, *args):
        if time.time() - self.t0 > 3:
            g.callExit = True

    def basic_file_frame(self, *args):
        self.stubCounter += 1
        if self.stubCounter > 50:
            g.callExit = True

    #Test: file_err_dir ----------------------------------

    def file_err_dir_frame(self, *args):
        self.stubCounter += 1
        if self.stubCounter > 50:
            g.callExit = True

    


#For collection by pytest ------------------------

def test_basic_dir():
    stage = GuiviewStagingClass()
    stage.basic()

def test_basic_file():
    stage = GuiviewStagingClass()
    stage.basic_file()

def test_true_positive():
    stage = GuiviewStagingClass()
    stage.true_positive()

def test_file_err():
    stage = GuiviewStagingClass()
    stage.file_err()

def test_file_err_dir():
    stage = GuiviewStagingClass()
    stage.file_err_dir()


if __name__ == "__main__":
    test_file_err()

