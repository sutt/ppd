import sys
import cv2
'''
Analyze the problem with imshow window become unresponsive "Not Responding"

basic3 shows the problem is when a loop stops executing imshow for ~5s it gets mad
'''

def basic():
    inputDir = "data/proc/hello-training-data/output4.avi"

    cam = cv2.VideoCapture(inputDir)

    ret, frame = cam.read()

    while(True):
        cv2.imshow('win', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            sys.exit()

def basic2():

    from modules.GuiC import GuiC

    gui = GuiC()

    inputDir = "data/proc/hello-training-data/output4.avi"

    cam = cv2.VideoCapture(inputDir)

    ret, frame = cam.read()

    while(True):
        cv2.imshow('win', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            sys.exit()


def basic3():

    # from modules.GuiC import GuiC

    # gui = GuiC()

    inputDir = "data/proc/hello-training-data/output4.avi"

    cam = cv2.VideoCapture(inputDir)

    ret, frame = cam.read()

    i = 0
    while(True):
        i+=1

        if i == 500:
            print '500...'
        elif i > 500:
            pass
        else:
            #won't be called after 500, imshow will complain
            cv2.imshow('win', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                sys.exit()




if __name__ == "__main__":

    # basic()
    # basic2()
    basic3()        #this one breaks, when you don't touch the windows for long