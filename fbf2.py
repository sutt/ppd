import cv2
import time, random
import os, sys
import argparse

print os.getcwd()
print 'hey'

ap = argparse.ArgumentParser()
path = "fps30.h264"
ap.add_argument("--file", type=str, default=path)

ap.add_argument("--writepath", type=str, default="")
ap.add_argument("--writebook", type=bool, default=True)

ap.add_argument("--refresh", type=int, default=1)
ap.add_argument("--interactive", type=bool, default=True)

ap.add_argument("--evalall", type=bool, default=False)
ap.add_argument("--printframes", type=bool, default=False)
ap.add_argument("--reporting", type=bool, default=True)

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


default_book = "book" + str(random.random()) + ".html"

def writebook(jpg_list, writepath, **kwargs):
    mybook = """<html>"""
    for jpg in jpg_list:
        mybook += '<img src="'
        mybook += jpg
        mybook += '"></img>'
    mybook += "</html>"
    bookname = kwargs.get("book", default_book )
    output_file = writepath + bookname
    f = open(output_file, 'w',)
    f.writelines(mybook)
    f.close()

i = 0
book_jpgs = []
i_bool = True
pause_bool = False
ret = True
t1 = time.time()
refresh0 = int(args["refresh"])
refresh = refresh0
writepath0 = args["writepath"]
writepath = writepath0
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
            
            
            
        key0 = cv2.waitKey(refresh)
        
        if key0 == ord('w'):
            print 'writing out current frame'
            pic_name = "pic" + str(random.uniform(1,10)) + ".jpg"
            cv2.imwrite(pic_name,frame)
            

            if args["writebook"]:
                book_jpgs.append(pic_name)
                writebook(book_jpgs,writepath)
            continue

        elif key0 == ord('e'):
            print 'advancing and writing'
        
        elif key0 == ord('o'):
            pass
            #input()  #options

        elif key0 == ord('a'):
            i -= 1
            print i
            print 'backing up'
            continue

        elif key0 == ord('s'):
            i += 1
            print i
            print 'advancing'
            continue
        
        elif key0 == ord('d'):
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
        
        elif key0 == ord('q'):
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
