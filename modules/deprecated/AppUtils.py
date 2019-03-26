import os, sys, time, copy, random, argparse
import traceback
import numpy as np
import cv2
import imutils

writepath = "data/write/oct"

def uni_file(inp_path,name="output",ext=".h264"):
    files = os.listdir(inp_path)
    i = 0
    while(True):
        i += 1
        fn = name + str(i) + ext
        if fn in files:
            continue
        else:
            return inp_path + "/" + fn

def uni_dir(inp_path,name="imgs",):
    dirs = [d for d in os.listdir(inp_path) 
            if os.path.isdir(os.path.join(inp_path, d))]
    i = 0
    while(True):
        i += 1
        dn = name + str(i)
        if dn in dirs:
            continue
        else:
            return dn

def make_dir(path):
    try:
        os.mkdir(path)
    except:
        print 'couldnt create new img subdir'

def write_pic(img, **kwargs):

    if kwargs.get('path',False):
        writepic_path = kwargs.get('path','')
    else:
        try:
            writepic_path = uni_dir(writepath)
            os.mkdir(writepath + '/' + writepic_path)
            print 'new img dir, ', str(writepic_path), ' at', str(writepath)
        except:
            print 'couldnt create new img subdir'

    p = writepath + "/" + writepic_path
    name_base = kwargs.get("name_base", "pic")
    if kwargs.get('randomize',True):
        pic_name = uni_file(p ,name=name_base,ext=".jpg")
    else:
        pic_name = str(name_base) + ".jpg"
    
    try:
        cv2.imwrite(pic_name,img)
    except:
        print 'couldnt write pic to path: ', p, 'as picname: ', pic_name
    
    return 0
    
