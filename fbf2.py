import cv2
import time, random
import os, sys
import argparse, traceback


ap = argparse.ArgumentParser()

ap.add_argument("--file", type=str, default="fps30.h264")
ap.add_argument("--writepath", type=str, default="")
ap.add_argument("--writebook", action="store_true")
ap.add_argument("--writebookinfo", action="store_true")
ap.add_argument("--picsize", type=str, default="")

ap.add_argument("--writebookvideo", action="store_true")

ap.add_argument("--refresh", type=int, default=1)
ap.add_argument("--interactive", action="store_true")

ap.add_argument("--printframes", action="store_true")
ap.add_argument("--reporting", action="store_true")


args = vars(ap.parse_args())


t0 = time.time()
print 'starting script...'


frames = []
j = 0
try:
    if args["interactive"]:
        vc = cv2.VideoCapture(args["file"])
        while(vc.isOpened()):
            try:
                ret,frame = vc.read()
                if ret:
                    frames.append(frame)
                    j += 1
                else:
                    print 'no ret num: ', str(j)
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

#default_book = "book" + str(random.random()) +     ".html"
writepath0 = args["writepath"]
writepath = writepath0
default_book = uni_file(writepath,name="book",ext=".html")
current_book = default_book

if args['writebookvideo']:
    
    output_ext = '.h264'
    output_vid_fn = uni_file(writepath,'outvid',output_ext)
    output_fps = 30
    output_size = (640,480)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    vw = cv2.VideoWriter(output_vid_fn,fourcc, output_fps, output_size)
    


if False:
    
    #vw = cv2.VideoWriter()
    print 'in here'
    try:
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        # have openh264-1.4.0-win64msvc.dll, but need openh264-1.4.0-win32msvc.dll
        #Please check environment and/or download library from here: https://github.com/cisco/openh264/releases
        #fourcc = cv2.VideoWriter_fourcc(*'X264')
        output_fps = 30
        output_size = (640,480)
        output_ext = '.h264'
        output_vid_fn = uni_file(writepath,'outvid',output_ext)
        #output_vid_fn = writepath + "/" + output_vid_fn
        
        out = cv2.VideoWriter(output_vid_fn,fourcc, output_fps, output_size)

        vc = cv2.VideoCapture(args["file"])
        print 'outputting here: ', str(output_vid_fn)
        while(vc.isOpened()):
            ret, frame = vc.read()
            if ret==True:
            
                #frame = cv2.flip(frame,0)
                out.write(frame)
            else:
                vc.release()
    except Exception as e:
        print 'error in vid write', str(e)

    
    vc.release()
    out.release()
    sys.exit()




def pause(dispTxt, breaker):
    while(True):
        inp = raw_input(dispTxt)
        return inp

def concat_dict(d):
    s = ""
    for key_x in d.iterkeys():
        s += " | "
        s += key_x
        s += " : "
        s += str( d.get(key_x,'') )
    return s

def writebook(jpg_list, writepath, bookname, **kwargs):
    
    info =  kwargs.get('info',[])
    if len(info)>0:
        b_info = True
        info_rev = info[:]
        info_rev.reverse()    
    
    mybook = """<html>"""
    for jpg in jpg_list:
        if b_info:
            frame_info = info_rev.pop()
            mybook += '<p>' + concat_dict(frame_info) + '</p>'   
        mybook += '<img src="'
        mybook += jpg
        mybook += '"'
        if len(args["picsize"]) > 0:
            mybook += ' ' + str(args['picsize']).split(',')[0] + \
                    '="' + str(args['picsize']).split(',')[1] + 'px"'
        mybook += '></img>'
    mybook += "</html>"
    
    output_file = writepath + bookname
    f = open(output_file, 'w',)
    f.writelines(mybook)
    f.close()
    return bookname


i = 0
book_jpgs = []
book_info = []
i_bool = True
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
            ret,frame = True, frames[i]
        else:
            if i_bool:
                ret,frame = vc.read()  
        
        if i_bool:
            i += 1

        if ret and (i >= 0):       
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
                frame_info = {}
                if args["writebookinfo"]:
                    frame_info['frame'] = i - 1
                    frame_info['shape'] = str( (shape1[0], shape1[1]) )
                    frame_info['orig_fn'] = args["file"]
                book_info.append(frame_info)
                book_jpgs.append(pic_name)
                writebook(book_jpgs,writepath,current_book,info=book_info)

            print 'writing out current frame num: ', str(i)
            continue

        elif key0 == ord('e'):
            
            pic_name = uni_file(writepath,name="pic",ext=".jpg")
            cv2.imwrite(pic_name,frame)
            
            if args["writebook"]:
                frame_info = {}
                if args["writebookinfo"]:
                    frame_info['bool'] = True
                    frame_info['frame'] = i - 1
                    frame_info['shape'] = str( (shape1[0], shape1[1]) )
                    frame_info['orig_fn'] = args["file"]
                book_info.append(frame_info)
                book_jpgs.append(pic_name)
                writebook(book_jpgs,writepath,current_book,info=book_info)

            if args["writebookvideo"]:
                
                if vw is None:
                    output_vid_fn = uni_file(writepath,'outvid',output_ext)
                    vw = cv2.VideoWriter(output_vid_fn,fourcc, output_fps, output_size)
                else:
                    vw.write(frame)

            print 'writing out current frame num: ', str(i)
            i += 1
            print i
            print 'advancing to ', str(i)
            
        
        elif key0 == ord('o'):

            while(True):
                ret = pause('options ... ', \
                             ['quit','newbook'])
                
                #print ret
                #strip_ret = str(ret) # filter(lambda char: char.isalpha(), ret)
                #print strip_ret
                #print strip_ret[0:len('newbook')]

                if ret == 'quit':
                    break
                
                elif ret[:7] == "newbook":
                    
                    if len(ret.split(' ')) > 1:
                        nb = writebook([],writepath, ret.split(' ')[1] )
                    else:
                        nb = writebook([],writepath, \
                                    uni_file(writepath,name="book",ext=".html"))
                    current_book = nb
                
                elif ret[:9] == "resetbook":
                    book_info = []
                    book_jpgs = []

                else:
                    print 'option <', str(ret),  '> not recognized'
            print 'quitting options...'



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
            pause_msg = "play" if i_bool else "paused"
            print pause_msg
            i -= 1  #weve already incremented after read
            if not(i_bool):
                refresh = 5000
            else:
                refresh = refresh0
            continue
        
        elif key0 == ord('q'):
            print 'quitting'
            break
        
        #/controls --------------------------------------------
        
        if args["interactive"] and (i == len(frames)):
            break   #exit on last frame

    except Exception as e:
        print 'exception in main loop', e.message
        #traceback.print_tb(e.__traceback__)
        print(traceback.format_exc())
        break

run_time = time.time() - t1
if args["reporting"]:
    print 'i: ', i
    print 'runtime: ', run_time
    print 'shape1: ', shape1
    print 'len(frames): ', len(frames)



vc.release()
cv2.destroyAllWindows()
vw.release()
