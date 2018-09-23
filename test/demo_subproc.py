import subprocess

'''
This is demo code for adding testing to gui view.

Notes:

    p.wait() waits for program to return, but we want to read it while it's happening

    timeout needs to wrap the subprocess in case program never exits

    timeout needs to interupt sleep, for example in frameDelay()

    stderr.readline() is a blocking call so need at least one line to be written

    can check subprocess is alive with poll() or can look for stdout secret message
'''

def launchProcess(strFlag):
    args = ["python", "demo_test.py"]
    args.append(strFlag)
    p = subprocess.Popen( args
                         ,stdout = subprocess.PIPE
                         ,stderr= subprocess.PIPE   
                        #,cwd
                    )
    return p

def watchProcess(p, b_poll=True):

    while(True):
        
        # if 'done with demo_test' in p.stdout.readline():
        #     print 'found secret message in stdout; breaking'
        #     break
        
        # problem: this is blocking, need to write something to 
        # stderr at end of script to ensure this can be past
        stderr_line = p.stderr.readline().strip()
        if stderr_line.find("script done") > -1:
            print stderr_line
            print 'found the secret message in stderr; breaking'
            break

        if  stderr_line != "":
            print stderr_line

        #if it doesnt exit quick enough, we go back to readline()
        if b_poll:
            if p.poll() is not None:
                print 'poll() did not return None'
                print 'program return code %s' % str(p.returncode)
                break
        
print '\ndefault:\n'
p = launchProcess("default")
watchProcess(p)

print "\nworking_msg:\n"
p = launchProcess("working_msg")
watchProcess(p)

print "\nworking_nomsg:\n"
p = launchProcess("working_nomsg")
watchProcess(p)

print "\nfailAssert:\n"
p = launchProcess("failAssert")
watchProcess(p)

print "\nthrowExcept:\n"
p= launchProcess("throwExcept")
watchProcess(p)

print "\ndoRaise:\n"
p = launchProcess("doRaise")
watchProcess(p)

print "\nstderr_msg:\n"
p = launchProcess("stderr_msg")
watchProcess(p)

print "\nstderr_msg (no poll):\n"
p = launchProcess("stderr_msg")
watchProcess(p, b_poll=False)

