import cv2
import time, random
import os, sys
import argparse


ap = argparse.ArgumentParser()
path = "fps30.h264"
ap.add_argument("--file", type=str, default=path)

ap.add_argument("--writepath", type=str, default="")
ap.add_argument("--writebook", action="store_true")
ap.add_argument("--writebookinfo", action="store_true")

ap.add_argument("--writebookvideo", action="store_true")

ap.add_argument("--refresh", type=int, default=1)
ap.add_argument("--interactive", action="store_true")

ap.add_argument("--printframes", action="store_true")
ap.add_argument("--reporting", action="store_true")

args = vars(ap.parse_args())


t0 = time.time()
print 'starting script...'
print 'print frames? ', args["printframes"]


frames = []
try:
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
except Exception as e:
    print 'exception in load frames ', e


def uni_file(inp_path,name="output",ext=".h264"):
    files = os.listdir(os.getcwd() + "/" + inp_path)
    i = 0
    while(True):
        i += 1
        fn = name + str(i) + ext
        if fn in files:
            continue
        else:
            return fn

#default_book = "book" + str(random.random()) + ".html"
writepath0 = args["writepath"]
writepath = writepath0
default_book = uni_file(writepath,name="book",ext=".html")



def concat_dict(d):
    s = ""
    for key_x in d.iterkeys():
        s += " | "
        s += key_x
        s += " : "
        s += str( d.get(key_x,'') )
    return s

def writebook(jpg_list, writepath, **kwargs):
    mybook = """<html>"""
    info =  kwargs.get('info',{})
    b_info = info.get('bool',False)
    for jpg in jpg_list:
        if b_info:
            mybook += '<p>' + concat_dict(info) + '</p>'   
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
i_last = -1
shape1 = 0

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

            if i == 1:
                shape1 = frame.shape
                print shape1
                
            if bool(args["printframes"]) and i != i_last:
                print i     
                i_last = i
            
        else:
            vc.release()    #last frame exit
            
        #controls ----------------------------------------------
        key0 = cv2.waitKey(refresh)
        
        if key0 == ord('w'):
            
            pic_name = uni_file(writepath,name="pic",ext=".jpg")
            cv2.imwrite(pic_name,frame)
            
            if args["writebook"]:
                book_info = {}
                if args["writebookinfo"]:
                    book_info['bool'] = True
                    book_info['frame'] = i
                    book_info['shape'] = str( (shape1[0], shape1[1]) )
                    book_info['orig_fn'] = args["file"]
                book_jpgs.append(pic_name)
                writebook(book_jpgs,writepath,info=book_info)

            print 'writing out current frame num: ', str(i)
            continue

        elif key0 == ord('e'):
            
            pic_name = uni_file(writepath,name="pic",ext=".jpg")
            cv2.imwrite(pic_name,frame)
            
            if args["writebook"]:
                frame_info = {}
                if args["writebookinfo"]:
                    frame_info['bool'] = True
                    frame_info['frame'] = i
                    frame_info['shape'] = str( (shape1[0], shape1[1]) )
                    frame_info['orig_fn'] = args["file"]
                book_jpgs.append(pic_name)
                writebook(book_jpgs,writepath,info=book_info)
            
            print 'writing out current frame num: ', str(i)
            i += 1
            print i
            print 'advancing to ', str(i)
            
        
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
        
        #/controls --------------------------------------------
        
        if args["interactive"] and (i == len(frames)):
            break   #exit on last frame

    except Exception as e:
        print 'exception in main loop', e
        break

run_time = time.time() - t1
if args["reporting"]:
    print 'i: ', i
    print 'runtime: ', run_time
    print 'shape1: ', shape1
    print 'len(frames): ', len(frames)

vc.release()
cv2.destroyAllWindows()
