import cv2
import time
import os, sys
import argparse

print os.getcwd()
print 'hey'

ap = argparse.ArgumentParser()
path = "fps30.h264"
ap.add_argument("--file", type=str, default=path)

ap.add_argument("--refresh", type=int, default=1)
ap.add_argument("--interactive", type=bool, default=True)

ap.add_argument("--evalall", type=bool, default=False)
ap.add_argument("--printframes", type=bool, default=False)
ap.add_argument("--reporting", type=bool, default=True)

ap.add_argument("--controls", type=bool, default=False)

ap.add_argument("--timems", type=int, default=1000)

args = vars(ap.parse_args())

print 'print frames? ', args["printframes"]
t0 = time.time()

frames = []
if args["interactive"]:
    vc = cv2.VideoCapture(args["file"])
    while(vc.isOpened()):
        try:
            ret,frame = vc.read()
            if ret:
                frames.append(frame)
            else:
                vc.release()
        except Exception as e:
            print 'exception loading frames', e
    print 'loaded ', len(frames), ' frames in secs ', time.time() - t0

#dir_to_write = func(getcwd)

i = 0
i_bool = True
pause_bool = False
ret = True
t1 = time.time()
refresh0 = int(args["refresh"])
refresh = refresh0
i_last = -1

vc = cv2.VideoCapture(args["file"])
while(vc.isOpened()):
    
    try:
        if args["interactive"]:
            if not(pause_bool):
                ret,frame = True, frames[i]    
            else:
                pause_bool = False
        else:
            if i_bool:
                ret,frame = vc.read()
                
        
        if i_bool:
            i += 1

        if ret and (i > 0):       
            cv2.imshow('frame',frame)
            #cv2.imwrite

            if i == 1 or args["evalall"]:
                print frame.shape
                shape1 = frame.shape
                
            if args["printframes"] and i != i_last:
                print i     
                i_last = i
            
        else:
            vc.release()
        
        if args["controls"]:
            timea = time.time()
            if cv2.waitKey(refresh) == ord('w'):
                print 'writing out current frame'
                #PrintFunc(frame,**kwargs)
                continue

            if cv2.waitKey(refresh) == ord('e'):
                print 'advancing and writing'
            if cv2.waitKey(refresh) == ord('o'):
                pass
                #input()  #options

            if cv2.waitKey(refresh) == ord('a'):
                i -= 1
                print i
                print 'backing up'
                continue

            if cv2.waitKey(refresh) == ord('s'):
                i += 1
                print i
                print 'advancing'
                continue
            
            if cv2.waitKey(refresh) == ord('d'):
                i_bool = False if i_bool else True
                pause_bool = True if not i_bool else False
                pause_msg = "play" if i_bool else "paused"
                print pause_msg
                if not(i_bool):
                    refresh = 5000
                else:
                    refresh = refresh0
                time.sleep(1)
                continue

            print time.time() - timea
        if cv2.waitKey(refresh) & 0xFF == ord('q'):
            print 'quitting'
            break
        
        if i == len(frames):
            break

    except Exception as e:
        print e
        print 'excepted expected'
        break

run_time = time.time() - t1
if args["reporting"]:
    print 'i: ', i
    print 'runtime: ', run_time
    print 'shape1: ', shape1
    print 'len(frames): ', len(frames)

vc.release()
cv2.destroyAllWindows()
