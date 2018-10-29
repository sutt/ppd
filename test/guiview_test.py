import os, sys, copy, json
import subprocess
import time

sys.path.append("../")
from modules.ControlFlow import FrameFactory
from modules.ControlFlow import TimeFactory
from modules.ControlFlow import DirectoryFactory
from modules.ControlDisplay import Display
from modules.DataSchemas import ScoreSchema
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
    [ ] modify watchProcess: not catching tests that error
        [ ] returncode is always 1 b/c error thrown in stub.exitByStr()

    Tests:

    [ ] Need to check frame pixel values against a benchmark: a diff


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

            if you don't create custom function for these, they will default to dummy

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

        #return code is valuable to see if test itself has an error
        #that disrupts execution, and thus doesn't create an Assertion Error
        #but does throw an error. This doesn't help right now because
        #all  subproc's should throw an error onExit.
        ret = 0
        for ten_milli_sec_step in range(100):
            if proc.poll() is not None:
                ret = proc.returncode
                break
            time.sleep(0.01)

        
        return stderrLog, ret


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
        
        msg, ret = self.watchProcess(p)

        bErrors = self.parseErrors(msg)

        if bErrors: #or ret != 0:
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
        
        msg, ret = self.watchProcess(p)

        bErrors = self.parseErrors(msg)

        if bErrors: #or ret != 0:
            print "\n".join(msg)
            raise Exception("TEST FAIL: basic_file")

    def true_positive(self):
        ''' verify that an assert within the subprocess gets caught here.
        '''

        cmd = '''python guiview.py --test true_positive --nogui --noshow 
                                    --file data/test/guiview/basic/output4.avi'''

        args = self.argsFromCmd(cmd)
        
        p = self.launchProcess(args)
        
        msg, ret = self.watchProcess(p)

        bErrors = self.parseErrors(msg)

        if not(bErrors):  #or ret != 0:
            print "\n".join(msg)
            raise Exception("TEST FAIL: true_positive (should have bErrors)")


    def file_err(self):
        ''' open an invalid --file, make sure it does exit but does so gracefully'''
        
        cmd = '''python guiview.py --test file_err --nogui --noshow 
                                    --file data/test/guiview/basic/notafn.avi'''

        args = self.argsFromCmd(cmd)
        
        p = self.launchProcess(args)
        
        msg, ret = self.watchProcess(p)

        bErrors = self.parseErrors(msg)

        if bErrors: #or ret != 0:
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
        
        msg, ret = self.watchProcess(p)

        bErrors = self.parseErrors(msg)

        if bErrors: # or ret != 0:
            print "\n".join(msg)
            raise Exception("TEST FAIL: fil_err_dir")

    def no_logs(self):
        ''' verifyb that .avi files even without .txt and .metalog files still run thru
        '''

        cmd = '''python guiview.py --test no_logs --nogui --noshow 
                                --dir data/test/guiview/no_logs/
                                --firstN 10'''

        args = self.argsFromCmd(cmd)
        
        p = self.launchProcess(args)
        
        msg, ret = self.watchProcess(p)

        bErrors = self.parseErrors(msg)

        if bErrors: # or ret != 0:
            print "\n".join(msg)
            raise Exception("TEST FAIL: no_logs")

    def advance_retreat(self):
        ''' verify that advance/retreat work on a --file run
        '''

        cmd = '''python guiview.py --test advance_retreat --nogui --noshow 
                                --file data/test/guiview/basic/output4.avi'''

        args = self.argsFromCmd(cmd)
        
        p = self.launchProcess(args)
        
        msg, ret = self.watchProcess(p)

        bErrors = self.parseErrors(msg)

        if bErrors: #or ret != 0:
            print "\n".join(msg)
            raise Exception("TEST FAIL: advance_retreat")

    def frame_sync(self):
        ''' verify that lag_tuple is sync'd with frame
        '''

        cmd = '''python guiview.py --test frame_sync --nogui --noshow 
                                --file data/test/guiview/frame_sync/output4.avi'''

        args = self.argsFromCmd(cmd)
        
        p = self.launchProcess(args)
        
        msg, ret = self.watchProcess(p)

        bErrors = self.parseErrors(msg)

        if bErrors: # or ret != 0:
            print "\n".join(msg)
            raise Exception("TEST FAIL: frame_sync")

    def true_time(self):
        ''' test that delayFrame() fires correctly; fuzzy assert bounds here to account
            for sometime considerable startup time'''

        cmd = '''python guiview.py --test true_time --nogui --noshow 
                                    --file data/test/guiview/basic/output4.avi'''

        args = self.argsFromCmd(cmd)
        
        p = self.launchProcess(args)
        
        msg, ret = self.watchProcess(p)

        bErrors = self.parseErrors(msg)

        if bErrors: # or ret != 0:
            print "\n".join(msg)
            raise Exception("TEST FAIL: true_time")

    def write_basic(self):
        ''' test that video output is created and written to'''

        cmd = '''python guiview.py --test write_basic --nogui --noshow 
                                    --file data/test/guiview/write_basic/output4.avi'''

        #Setup Test Data Dir -------------------------
        TEST_DATA_DIR = "../data/test/guiview/write_basic/"
        TEST_DATA_FN = "output4.proc1.avi"

        try:
            os.remove(os.path.join(TEST_DATA_DIR, TEST_DATA_FN))
        except:
            pass
        assert not(TEST_DATA_FN in os.listdir(TEST_DATA_DIR))

        #Run Test -----------------------------------
        args = self.argsFromCmd(cmd)
        
        p = self.launchProcess(args)
        
        msg, ret = self.watchProcess(p)

        bErrors = self.parseErrors(msg)

        #Test output data ---------------------------
        list_files = os.listdir(TEST_DATA_DIR)
        if not("output4.proc1.avi" in list_files):
            bErrors = True
            msg += ["TEST DATA: could not find output file in test data directory"]

        if not(bErrors):
            try:        
                output_size = os.path.getsize(os.path.join(TEST_DATA_DIR
                                                        ,TEST_DATA_FN))

                print 'OUTPUT SIZE:'
                print output_size
                print 3*10**5
                print output_size < 3*10**5
                if not((10**4) < output_size < 3*(10**5)): #between 10 kB and 300 kB
                    bErrors = True
                    msg += ["TEST DATA: output file size below/above level expected"]
            except:
                bErrors = True
                msg += ["TEST DATA: could not find size of the output file"]

        #Output test result
        if bErrors: # or ret != 0:
            print "\n".join(msg)
            raise Exception("TEST FAIL: write_basic")


    def write_adv(self):
        ''' test that video output is does not write without writeframe on'''

        cmd = '''python guiview.py --test write_adv --nogui --noshow 
                                    --file data/test/guiview/write_adv/output4.avi'''

        #Setup Test Data Dir -------------------------
        TEST_DATA_DIR = "../data/test/guiview/write_adv/"
        TEST_DATA_FN = "output4.proc1.avi"

        try:
            os.remove(os.path.join(TEST_DATA_DIR, TEST_DATA_FN))
        except:
            pass
        assert not(TEST_DATA_FN in os.listdir(TEST_DATA_DIR))

        #Run Test -----------------------------------
        args = self.argsFromCmd(cmd)
        
        p = self.launchProcess(args)
        
        msg, ret = self.watchProcess(p)

        bErrors = self.parseErrors(msg)

        #Test output data ---------------------------
        list_files = os.listdir(TEST_DATA_DIR)
        if not("output4.proc1.avi" in list_files):
            bErrors = True
            msg += ["TEST DATA: could not find output file in test data directory"]

        if not(bErrors):
            try:        
                output_size = os.path.getsize(os.path.join(TEST_DATA_DIR
                                                        ,TEST_DATA_FN))

                if not( 7*(10**3) < output_size < 4*(10**4)): #between 7 kB and 40 kB
                    bErrors = True
                    msg += ["TEST DATA: output file size below/above level expected"]
            except:
                bErrors = True
                msg += ["TEST DATA: could not find size of the output file"]

        #TODO - more tests: is each frame the same?
                #import frame factory? import diffSummary?

        #Output test result -------------------------
        if bErrors: # or ret != 0:
            print "\n".join(msg)
            raise Exception("TEST FAIL: write_adv")

    
    def write_two(self):
        ''' test that video output is does not write without writeframe on'''

        cmd = '''python guiview.py --test write_two --nogui --noshow 
                                    --file data/test/guiview/write_two/output6.avi'''

        #Setup Test Data Dir -------------------------
        TEST_DATA_DIR = "../data/test/guiview/write_two/"
        TEST_DATA_FN_1 = "output6.proc1.avi"
        TEST_DATA_FN_2 = "output6.proc2.avi"

        try:
            os.remove(os.path.join(TEST_DATA_DIR, TEST_DATA_FN_1))
            os.remove(os.path.join(TEST_DATA_DIR, TEST_DATA_FN_2))
        except:
            pass
        assert not(TEST_DATA_FN_1 in os.listdir(TEST_DATA_DIR))
        assert not(TEST_DATA_FN_2 in os.listdir(TEST_DATA_DIR))

        #Run Test -----------------------------------
        args = self.argsFromCmd(cmd)
        
        p = self.launchProcess(args)
        
        msg, ret = self.watchProcess(p)

        bErrors = self.parseErrors(msg)

        #Test output data ---------------------------
        list_files = os.listdir(TEST_DATA_DIR)
        if not(TEST_DATA_FN_1 in list_files) or not(TEST_DATA_FN_2 in list_files):
            bErrors = True
            msg += ["TEST DATA: could not find output files in test data directory"]

        if not(bErrors):
            try:        
                output_size_1 = os.path.getsize(os.path.join(TEST_DATA_DIR
                                                        ,TEST_DATA_FN_1))

                if not( 3*(10**4) < output_size_1 < 6*(10**4)): #between 30 kB and 60 kB
                    bErrors = True
                    msg += ["TEST DATA: output file size below/above level expected"]
                
                output_size_2 = os.path.getsize(os.path.join(TEST_DATA_DIR
                                                        ,TEST_DATA_FN_2))

                if not( 9*(10**5) < output_size_2 < 1.1*(10**6)): #between 900 kB and 1.1 MB
                    bErrors = True
                    msg += ["TEST DATA: output file size below/above level expected"]
            except:
                bErrors = True
                msg += ["TEST DATA: could not find size of the output file"]

        #Output test result
        if bErrors: # or ret != 0:
            print "\n".join(msg)
            raise Exception("TEST FAIL: write_adv")

    def write_time(self):
        ''' test that timelog gets written out, and that values are correct.
            here, we skip 3rd frame so time log should have frame1, frame2, 
            and frame4 values'''

        cmd = '''python guiview.py --test write_time --nogui --noshow 
                                    --file data/test/guiview/write_time/output4.avi'''

        #Setup Test Data Dir -------------------------
        TEST_DATA_DIR = "../data/test/guiview/write_time/"
        TEST_DATA_FN_1 = "output4.proc1.avi"
        TEST_DATA_FN_2 = "output4.proc1.txt"

        try:
            os.remove(os.path.join(TEST_DATA_DIR, TEST_DATA_FN_1))
            os.remove(os.path.join(TEST_DATA_DIR, TEST_DATA_FN_2))
        except:
            pass
        assert not(TEST_DATA_FN_1 in os.listdir(TEST_DATA_DIR))
        assert not(TEST_DATA_FN_2 in os.listdir(TEST_DATA_DIR))

        #Run Test -----------------------------------
        args = self.argsFromCmd(cmd)
        
        p = self.launchProcess(args)
        
        msg, ret = self.watchProcess(p)

        bErrors = self.parseErrors(msg)

        #Test output data ---------------------------
        list_files = os.listdir(TEST_DATA_DIR)
        if not(TEST_DATA_FN_1 in list_files) or not(TEST_DATA_FN_2 in list_files):
            bErrors = True
            msg += ["TEST DATA: could not find output files in test data directory"]

        if not(bErrors):
            try:
                with open(os.path.join(TEST_DATA_DIR, TEST_DATA_FN_2), 'r') as f:
                    lines = f.readlines()
                assert len(lines) == 3
                assert float(lines[0]) == 0
                assert float(lines[1]) == 0.0329
                assert float(lines[2]) == 0.0309

            except:
                bErrors = True
                msg += ["TEST DATA: timelog file is not as expected"]
                msg += [str(lines)]

        #Output test result
        if bErrors: # or ret != 0:
            print "\n".join(msg)
            raise Exception("TEST FAIL: write_time")

    def write_bad_time(self):
        ''' test that timelog gets written out, even when existing timelog
            is bad or doesn't exist: output5.txt is blank and output6.txt
            does not exist, verify there is an output framelog with zeros '''

        #Setup Test Data Dir -------------------------
        TEST_DATA_DIR = "../data/test/guiview/write_time/"
        TEST_DATA_FN_1_VID = "output5.proc1.avi"
        TEST_DATA_FN_1 = "output5.proc1.txt"
        TEST_DATA_FN_2_VID = "output6.proc1.avi"
        TEST_DATA_FN_2 = "output6.proc1.txt"

        try:
            os.remove(os.path.join(TEST_DATA_DIR, TEST_DATA_FN_1))
            os.remove(os.path.join(TEST_DATA_DIR, TEST_DATA_FN_2))
            os.remove(os.path.join(TEST_DATA_DIR, TEST_DATA_FN_1_VID))
            os.remove(os.path.join(TEST_DATA_DIR, TEST_DATA_FN_2_VID))
        except:
            print 'cant remove files'
            # sys.exit()
        assert not(TEST_DATA_FN_1 in os.listdir(TEST_DATA_DIR))
        assert not(TEST_DATA_FN_2 in os.listdir(TEST_DATA_DIR))
        assert not(TEST_DATA_FN_1_VID in os.listdir(TEST_DATA_DIR))
        assert not(TEST_DATA_FN_2_VID in os.listdir(TEST_DATA_DIR))

        #Run Test #1 -----------------------------------
        cmd = '''python guiview.py --test write_bad_time --nogui --noshow 
                                    --file data/test/guiview/write_time/output5.avi'''
        args = self.argsFromCmd(cmd)
        
        p = self.launchProcess(args)
        
        msg, ret = self.watchProcess(p)

        bErrors = self.parseErrors(msg)

        #Test output data ---------------------------
        list_files = os.listdir(TEST_DATA_DIR)
        if not(TEST_DATA_FN_1 in list_files):
            bErrors = True
            msg += ["TEST DATA: could not find output files in test data directory"]

        if not(bErrors):
            try:
                with open(os.path.join(TEST_DATA_DIR, TEST_DATA_FN_1), 'r') as f:
                    lines = f.readlines()
                assert len(lines) == 3
                assert float(lines[0]) == 0
                assert float(lines[1]) == 0

            except:
                bErrors = True
                msg += ["TEST DATA: timelog file is not as expected"]
                msg += [str(lines)]

        #Output test result
        if bErrors: # or ret != 0:
            print "\n".join(msg)
            raise Exception("TEST FAIL: write_bad_time")

        #Run Test #2 -----------------------------------
        cmd = '''python guiview.py --test write_bad_time --nogui --noshow 
                                    --file data/test/guiview/write_time/output6.avi'''
        args = self.argsFromCmd(cmd)
        
        p = self.launchProcess(args)
        
        msg, ret = self.watchProcess(p)

        bErrors = self.parseErrors(msg)

        #Test output data ---------------------------
        list_files = os.listdir(TEST_DATA_DIR)
        if not(TEST_DATA_FN_1 in list_files):
            bErrors = True
            msg += ["TEST DATA: could not find output files in test data directory"]

        if not(bErrors):
            try:
                with open(os.path.join(TEST_DATA_DIR, TEST_DATA_FN_2), 'r') as f:
                    lines = f.readlines()
                assert len(lines) == 3
                assert float(lines[0]) == 0
                assert float(lines[1]) == 0

            except:
                bErrors = True
                msg += ["TEST DATA: timelog file is not as expected"]
                msg += [str(lines)]

        #Output test result
        if bErrors: # or ret != 0:
            print "\n".join(msg)
            raise Exception("TEST FAIL: write_bad_time")

    
    def meta_basic(self):
        ''' test that metalog gets written out. and test associated values'''

        #Setup Test Data Dir -------------------------
        TEST_DATA_DIR = "../data/test/guiview/meta_basic/"
        TEST_DATA_FN_VID = "output4.proc1.avi"
        TEST_DATA_FN_TXT = "output4.proc1.txt"
        TEST_DATA_FN = "output4.proc1.metalog"
        

        try:
            os.remove(os.path.join(TEST_DATA_DIR, TEST_DATA_FN))
            os.remove(os.path.join(TEST_DATA_DIR, TEST_DATA_FN_TXT))
            os.remove(os.path.join(TEST_DATA_DIR, TEST_DATA_FN_VID))
        except:
            pass
        assert not(TEST_DATA_FN in os.listdir(TEST_DATA_DIR))
        assert not(TEST_DATA_FN_TXT in os.listdir(TEST_DATA_DIR))
        assert not(TEST_DATA_FN_VID in os.listdir(TEST_DATA_DIR))

        cmd = '''python guiview.py --test meta_basic --nogui --noshow --allowduplicates
                                    --file data/test/guiview/meta_basic/output4.avi'''
        args = self.argsFromCmd(cmd)
        
        p = self.launchProcess(args)
        
        msg, ret = self.watchProcess(p)

        bErrors = self.parseErrors(msg)

        #Test output data ---------------------------
        list_files = os.listdir(TEST_DATA_DIR)
        if not(TEST_DATA_FN in list_files):
            bErrors = True
            msg += ["TEST DATA: could not find output files in test data directory"]

        if not(bErrors):
            try:
                with open(os.path.join(TEST_DATA_DIR, TEST_DATA_FN), 'r') as f:
                    lines = f.readlines()
                assert len(lines) > 0

                line = ''.join(lines)
                json_data = json.loads(line)

                assert len(json_data['notes']['basic_notes']) > 0

                assert json_data['processed'] == True

                assert json_data['notes']['orientation'] == 0

                assert len(json_data['frames']) > 0

                #save three frames: indexes 0,2,2
                assert json_data['frames'][0]['orig_vid_index'] == 0
                assert json_data['frames'][1]['orig_vid_index'] == 2
                assert json_data['frames'][2]['orig_vid_index'] == 2

                assert len(json_data['frames'][2]['frame_type']) > 0
                
            except Exception as e:
                bErrors = True
                msg += ["TEST DATA: metalog file is not as expected"]
                msg += [str(line)]
                msg += [e.message]

        #Output test result
        if bErrors: # or ret != 0:
            print "\n".join(msg)
            raise Exception("TEST FAIL: meta_basic")

    def meta_adv(self):
        ''' test metalog:
                -writes out even without an associated metalog for orig vid
                -custom frameloginput (in the test data dir itself) via --framelog
                -write two separate outputs: check framelog doesn't overlap
        '''

        #Setup Test Data Dir -------------------------
        TEST_DATA_DIR = "../data/test/guiview/meta_adv/"
        TEST_DATA_FN_1_ALL = ["output6.proc1.avi", "output6.proc1.txt", "output6.proc1.metalog"]
        TEST_DATA_FN_2_ALL = ["output6.proc2.avi", "output6.proc2.txt", "output6.proc2.metalog"]
        TEST_DATA_FN_1 = "output6.proc1.metalog"
        TEST_DATA_FN_2 = "output6.proc2.metalog"
        
        test_fns = TEST_DATA_FN_1_ALL
        test_fns.extend(TEST_DATA_FN_2_ALL)
        
        for f in test_fns:
            try:
                os.remove(os.path.join(TEST_DATA_DIR, f))
            except:
                pass
        for f in test_fns:
            assert not(f in os.listdir(TEST_DATA_DIR))
        

        cmd = '''python guiview.py --test meta_adv --nogui --noshow 
                            --file data/test/guiview/meta_adv/output6.avi
                            --framelog data/test/guiview/meta_adv/guiview-custom.jsonc'''
        
        args = self.argsFromCmd(cmd)
        
        p = self.launchProcess(args)
        
        msg, ret = self.watchProcess(p)

        bErrors = self.parseErrors(msg)

        #Test output data ---------------------------
        list_files = os.listdir(TEST_DATA_DIR)
        if not(TEST_DATA_FN_1 in list_files) or not(TEST_DATA_FN_2 in list_files):
            bErrors = True
            msg += ["TEST DATA: could not find output files in test data directory"]

        if not(bErrors):
            try:
                
                #1st metalog
                with open(os.path.join(TEST_DATA_DIR, TEST_DATA_FN_1), 'r') as f:
                    lines = f.readlines()
                line = ''.join(lines)
                json_data = json.loads(line)

                assert json_data.get('notes', None) is None

                assert len(json_data['frames']) == 2
                
                assert json_data['frames'][0]['orig_vid_index'] == 0
                assert json_data['frames'][1]['orig_vid_index'] == 1

                assert json_data['frames'][0]['frame_type'] == "test meta_adv"

                #2nd metalog
                with open(os.path.join(TEST_DATA_DIR, TEST_DATA_FN_2), 'r') as f:
                    lines = f.readlines()
                line = ''.join(lines)
                json_data = json.loads(line)

                assert json_data.get('notes', None) is None

                assert len(json_data['frames']) == 3

                assert json_data['frames'][0]['orig_vid_index'] == 2
                assert json_data['frames'][1]['orig_vid_index'] == 3
                assert json_data['frames'][2]['orig_vid_index'] == 4

                assert json_data['frames'][1]['notes'] == "use this for testing custom framelogs with the --framelog flag"                
                
            except Exception as e:
                bErrors = True
                msg += ["TEST DATA: metalog file is not as expected"]
                msg += [str(line)]
                msg += [str(e)]

        #Output test result
        if bErrors: # or ret != 0:
            print "\n".join(msg)
            raise Exception("TEST FAIL: meta_adv")

    def write_score(self):
        ''' test meta log score output: use a stub to mimin do a selectROI for a 
            "hand-drawn" score and see if that gets output into metalog.
            
                details: frame1 should have a score
                         frame2 should have no score
                         frame3 should have a repeat of frame1 score
                         
        '''

        cmd = '''python guiview.py --test write_score --nogui --noshow 
                                    --file data/test/guiview/write_score/output4.avi'''

        #Setup Test Data Dir -------------------------
        TEST_DATA_DIR = "../data/test/guiview/write_score/"
        TEST_DATA_FN = "output4.proc1.metalog"
        TEST_DATA_ALL = ["output4.proc1.avi", "output4.proc1.txt", "output4.proc1.metalog"]

        for f in TEST_DATA_ALL:
            try:
                os.remove(os.path.join(TEST_DATA_DIR, f))
            except:
                pass
        for f in TEST_DATA_ALL:
            assert not(f in os.listdir(TEST_DATA_DIR))

        #Run Test -----------------------------------
        args = self.argsFromCmd(cmd)
        
        p = self.launchProcess(args)
        
        msg, ret = self.watchProcess(p)

        bErrors = self.parseErrors(msg)

        #Test output data ---------------------------
        list_files = os.listdir(TEST_DATA_DIR)
        if not(TEST_DATA_FN in list_files):
            bErrors = True
            msg += ["TEST DATA: could not find output file in test data directory"]

        #Assess output for details ------------------
        if not(bErrors):
            try:        
                
                with open(os.path.join(TEST_DATA_DIR, TEST_DATA_FN), 'r') as f:
                    lines = f.readlines()
                line = ''.join(lines)
                json_data = json.loads(line)

                assert json_data.get('frames', None) is not None
                assert len(json_data['frames']) == 3
                
                scoring = json_data['frames'][0]['scoring']
                assert scoring is not None
                assert scoring.get('0').get('type') == 'circle'
                assert scoring.get('0').get('data') == [100,100,50,60]

                scoring = json_data['frames'][1]['scoring']
                assert scoring is None

                scoring = json_data['frames'][2]['scoring']
                assert scoring is not None
                assert scoring.get('0').get('type') == 'circle'
                assert scoring.get('0').get('data') == [100,100,50,60]

            except Exception as e:
                bErrors = True
                msg += ["TEST DATA: metalog / metalog data is not as expected"]
                msg += [str(e.message)]
                # msg += [sys.tr]

        #Output test result -------------------------
        if bErrors:
            print "\n".join(msg)
            raise Exception("TEST FAIL: write_score")

    



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
        elif strTest == 'no_logs':
            self.no_logs_data()
        elif strTest == 'true_time':
            self.true_time_data()
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
        elif strTest == 'no_logs':
            return self.no_logs_frame
        elif strTest == 'advance_retreat':
            return self.advance_retreat_frame
        elif strTest == 'frame_sync':
            return self.frame_sync_frame
        elif strTest == 'true_time':
            return self.true_time_frame
        else:
            return self.dummy

    def vidByStr(self, strTest):

        if strTest == "basic":
            return self.dummy
        elif strTest == "file_err":
            return self.file_err_vid
        elif strTest == "true_time":
            return self.true_time_vid
        else:
            return self.dummy

    def exitByStr(self, strTest):
        
        if strTest == "basic":
             return self.basic_exit
        elif strTest == "file_err_dir":
            return self.file_err_dir_exit
        elif strTest == "no_logs":
            return self.no_logs_data
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
                    ,_display
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
                            ,_display
                            ):
        
        #this opens on pause, frame counter should start here,
        #and continue to remain here.
        assert _frameFactory.getFrameCounter() ==  0
            
    def true_positive_frame( self, 
                            _frameFactory
                            ,_timeFactory
                            ,_directoryFactory
                            ,_display
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
                        ,_display
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
                            ,_display
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


    def no_logs_data(self):
        self.requestedVids = ["output4.avi", "output5.avi"]
        
        #two copies of each
        self.requestedVids += copy.copy(self.requestedVids)

    def no_logs_frame( self
                            ,_frameFactory
                            ,_timeFactory
                            ,_directoryFactory
                            ,_display
                            ):

        if _frameFactory.getFrameCounter() == 5:
        
            vidFn = _directoryFactory.vidFn()

            if vidFn in self.requestedVids:

                self.requestedVids.pop(self.requestedVids.index(vidFn))

        self.mockCounter += 1


    def no_logs_exit(self):
        
        #both videos have been popped twice
        assert len(self.requestedVids) == 0

    def advance_retreat_frame( self
                            ,_frameFactory
                            ,_timeFactory
                            ,_directoryFactory
                            ,_display
                            ):

        # verify that frame advances and retreats,
        # verify that frame never goes below zero
        # verfiy that fast forward advances 10 frames
        
        currentFrame = _frameFactory.getFrameCounter()
        mockCounter = self.mockCounter
        
        if mockCounter < 5:
        
            assert currentFrame == self.mockCounter #+ 1

        elif 5 <= mockCounter <= 10:
            
            assert currentFrame == max(0, 8 - self.mockCounter)

        elif mockCounter  == 11:

            assert currentFrame == 10

        self.mockCounter += 1

    def frame_sync_frame( self
                            ,_frameFactory
                            ,_timeFactory
                            ,_directoryFactory
                            ,_display
                            ):
        
        if self.mockCounter == 4:
        
            assert _frameFactory.getFrameCounter() == 5

            assert 0.4 > _timeFactory.lag_tuple()[1] > 0.3
            assert 0.05 > _timeFactory.lag_tuple()[0] > 0.02

        if self.mockCounter == 5:
        
            assert _frameFactory.getFrameCounter() == 5

            assert 0.4 > _timeFactory.lag_tuple()[0] > 0.3
            assert 0.04 > _timeFactory.lag_tuple()[1] > 0.01
        
        self.mockCounter += 1

    def true_time_data(self):
        self.t0 = None
    
    def true_time_frame(self, *args):
        if self.t0 is None:
            self.t0 = time.time()   #note first frame
    
    def true_time_vid(self, *args):
                        # ,_frameFactory
                        # ,_timeFactory
                        # ,_directoryFactory
                        # ,_display
                        # ):
        
        if self.mockCounter == 0:
            #this video, output4.avi, is 12.89 seconds long
            #this interval at least assures us we aren't running with nodelay on
            #or some kind of inter
            assert 13.0 > time.time() - self.t0 > 12.5

        #only test first run thru
        self.mockCounter += 1



        

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
        elif strTest == "no_logs":
            return self.no_logs_frame
        elif strTest == "advance_retreat":
            return self.advance_retreat_frame
        elif strTest == "frame_sync":
            return self.frame_sync_frame
        elif strTest == 'write_basic':
            return self.write_basic_frame
        elif strTest == 'write_adv':
            return self.write_adv_frame
        elif strTest == 'write_two':
            return self.write_two_frame
        elif strTest == 'write_time':
            return self.write_time_frame
        elif strTest == 'write_bad_time':
            return self.write_time_frame    #same as other test
        elif strTest == 'meta_basic':
            return self.meta_basic_frame
        elif strTest == 'meta_adv':
            return self.meta_adv_frame
        elif strTest == 'write_score':
            return self.write_score_frame
        else:
            return self.dummy

    def vidByStr(self, strTest):

        if strTest == "basic":
            return self.basic_vid
        elif strTest == "true_time":
            return self.true_time_vid
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

    #Test Stub: file_err_dir ----------------------------------

    def file_err_dir_frame(self, *args):
        self.stubCounter += 1
        if self.stubCounter > 50:
            g.callExit = True

    def no_logs_frame(self, *args):
        self.stubCounter += 1
        if self.stubCounter > 50:
            g.callExit = True

    #Test Stub: advance_retreat ---------------------------------

    def advance_retreat_frame(self, *args):
                            # ,_frameFactory
                            # ,_timeFactory
                            # ,_directoryFactory
                            # ,_display
                            # ):
        
        if self.stubCounter < 5:
            g.switchAdvanceFrame = True
        
        elif 5 <= self.stubCounter <= 10:
            g.switchRetreatFrame = True
        
        elif self.stubCounter == 11:
            g.switchFastforward = True

        self.stubCounter += 1

        if self.stubCounter > 20:
            g.callExit = True

    
    def true_time_vid(self, *args):
        
        #need to start froma paused state
        g.playOn = True
        
        self.stubCounter += 1
        
        #exit after first run thru
        if self.stubCounter > 1:
            g.callExit = True

    #Test Stub: write_basic --------------------

    def write_basic_frame(self, *args):
        
        if self.stubCounter == 1:
            g.initWriteVid = True

        if self.stubCounter == 2:
            g.writevidOn = True

        if 2 < self.stubCounter < 20:
            g.switchAdvanceFrame = True
        
        self.stubCounter += 1
        
        if self.stubCounter > 25:
            g.callExit = True

    
    def write_adv_frame(self, *args):
        
        if self.stubCounter == 1:
            g.initWriteVid = True

        if self.stubCounter == 2:
            g.writevidOn = True

        if 2 < self.stubCounter < 25:
            g.switchAdvanceFrame = True

        if self.stubCounter == 5:
            g.writevidOn = False
        
        self.stubCounter += 1
        
        if self.stubCounter > 25:
            g.callExit = True

    def write_two_frame(self, *args):
        
        if self.stubCounter == 1:
            g.initWriteVid = True

        if 1 < self.stubCounter < 4:
            g.switchWriteVid = True

        if self.stubCounter == 5:
            g.initWriteVid = True
            g.writevidOn = True
            g.playOn = True

        self.stubCounter += 1
        
        if self.stubCounter > 25:
            g.callExit = True

    def write_time_frame(self, *args):
        
        # this could be wrong as of frameFactory.advanceAndWrite change to 
        # advance frame after each write automatically

        if self.stubCounter == 1:
            g.initWriteVid = True

        if self.stubCounter == 2:
            g.switchWriteVid = True

        if self.stubCounter == 3:
            g.switchAdvanceFrame = True

        if self.stubCounter == 4:
            g.switchWriteVid = True

        if self.stubCounter == 5:
            g.switchAdvanceFrame = True

        if self.stubCounter == 6:
            g.switchAdvanceFrame = True

        if self.stubCounter == 7:
            g.switchWriteVid = True

        self.stubCounter += 1
        
        if self.stubCounter > 25:
            g.callExit = True
    

    def meta_basic_frame(self, *args):
        
        if self.stubCounter == 1:
            g.initWriteVid = True

        if self.stubCounter == 2:
            g.switchWriteVid = True     #frame0

        if self.stubCounter == 3:
            # g.switchAdvanceFrame = True
            pass

        if self.stubCounter == 4:
            g.switchAdvanceFrame = True
            #keep this one, we advance additional frame
            
        if self.stubCounter == 5:
            g.switchWriteVid = True     #frame2
            
        if self.stubCounter == 6:
            g.switchRetreatFrame = True     #back a frame b/c we've advanced

        if self.stubCounter == 7:
            g.switchWriteVid = True     #frame2

        self.stubCounter += 1
        
        if self.stubCounter > 10:
            g.callExit = True

    def meta_adv_frame(self, *args):
        
        if self.stubCounter == 1:
            g.initWriteVid = True       #out0

        if self.stubCounter == 2:
            g.switchWriteVid = True     #frame0->out0

        if self.stubCounter == 3:
            # g.switchAdvanceFrame = True
            pass

        if self.stubCounter == 4:
            g.switchWriteVid = True     #frame1->out1
            
        if self.stubCounter == 5:
            g.initWriteVid = True       #out1

        if self.stubCounter == 6:
            # g.switchAdvanceFrame = True
            pass
            
        if self.stubCounter == 7:
            g.switchWriteVid = True     #frame2->out1
        
        if self.stubCounter == 8:
            # g.switchAdvanceFrame = True
            pass
            
        if self.stubCounter == 9:
            g.switchWriteVid = True     #frame3->out1

        if self.stubCounter == 10:
            # g.switchAdvanceFrame = True
            pass
            
        if self.stubCounter == 11:
            g.switchWriteVid = True     #frame4->out1

        self.stubCounter += 1
        
        if self.stubCounter > 15:
            g.callExit = True
    

    def write_score_frame(self
                        ,_frameFactory
                        ,_timeFactory
                        ,_directoryFactory
                        ,_display
                        ):
        
        if self.stubCounter == 1:
            g.initWriteVid = True      

        if self.stubCounter == 2:
            
            outputScore = ScoreSchema()
            roiStub = (100,100,50,60)
            outputScore.addCircle(roiStub, objEnum = 0)
            _display._test_set_outputScore(copy.deepcopy(outputScore))

            g.switchWriteScoring = True
        
        if self.stubCounter == 3:
            g.switchWriteVid = True   #don't write scoring data

        if self.stubCounter == 4:
            g.switchWriteScoring = True #write scoring data, is it carried over from 2-frames-before?

        self.stubCounter += 1
        
        if self.stubCounter > 5:
            g.callExit = True
    


#For collection by pytest ------------------------

def test_write_score():
    stage = GuiviewStagingClass()
    stage.write_score()

def test_meta_adv():
    stage = GuiviewStagingClass()
    stage.meta_adv()

def test_meta_basic():
    stage = GuiviewStagingClass()
    stage.meta_basic()

def test_write_bad_time():
    stage = GuiviewStagingClass()
    stage.write_bad_time()

def test_write_time():
    stage = GuiviewStagingClass()
    stage.write_time()

def test_write_two():
    stage = GuiviewStagingClass()
    stage.write_two()

def test_write_basic():
    stage = GuiviewStagingClass()
    stage.write_basic()

def test_write_adv():
    stage = GuiviewStagingClass()
    stage.write_adv()

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

def test_no_logs():
    stage = GuiviewStagingClass()
    stage.no_logs()

def test_advance_retreat():
    stage = GuiviewStagingClass()
    stage.advance_retreat()

def test_frame_sync():
    stage = GuiviewStagingClass()
    stage.frame_sync()

def test_true_time():
    stage = GuiviewStagingClass()
    stage.true_time()

if __name__ == "__main__":
    test_write_score()
    pass

