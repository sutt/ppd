import sys
import time

class TestMe:

    def __init__(self):
        self.data = None

    def failAssert(self):
        assert False
    
    def throwExcept(self):
        try:
            a = [1]
            b = a[2]
        except Exception as e:
            print 'caught in except! msg:'
            print e
            print '\n'

    def doRaise(self):
        raise Exception("My Exception")
    
    def mainSleep(self):
        print 'sleeping for 3 secs...'
        time.sleep(3)

class ExitException(Exception):
    def __init__(self):
        Exception.__init__(self,"script done") 

if __name__ == "__main__":

    run_type = "default"
    if (sys.argv) > 0:
        run_type = sys.argv[1]

    if run_type == "default":
        
        print 'in demo_test default run'
        testme = TestMe()
        testme.mainSleep()
        print 'done with demo_test'

    elif run_type == "working_msg":
        testme = TestMe()
        print 'done with demo_test'

    elif run_type == "working_nomsg":
        testme = TestMe()

    elif run_type == "failAssert":
        testme.failAssert()

    elif run_type == "throwExcept":
        testme = TestMe()
        testme.throwExcept()

    elif run_type == "doRaise":
        testme = TestMe()
        testme.doRaise()

    elif run_type == "stderr_msg":
        testme = TestMe()
        # testme.doRaise()
        # raise ExitException
        raise Exception("script done")
        # time.sleep(1)

    else:
        print 'couldnt find that run_type, not running anything...'
