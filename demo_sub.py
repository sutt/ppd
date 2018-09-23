import time
import subprocess

def demo(self):
    ''' verify that multi vids run in a --dir run'''
    
    args = []
    args += ["python"]
    args += ["guiview.py"]
    # args += ["--test"]
    # args += ["basic"]
    # args += ["--noshow"]
    args += ["--nogui"]
    args += ["--dir"]
    args += ["data/test/guiview/basic/"]
    
    try:
        p = subprocess.Popen(args
                            # ,stderr = subprocess.PIPE
                            # ,stdout = subprocess.PIPE
                            # ,cwd = "../"
                            )
    except Exception as e:
        print 'err:'
        print e.message
        
    p.wait()
    if p.poll() is None:
        print 'p is done'

    time.sleep(4)
    # msg = self.watchProcess(p)

    # print msg
    # print noErrors

demo(1)