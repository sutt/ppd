from matplotlib import pyplot as plt
import numpy as np
import cv2
import os, sys, time, argparse
import requests
from PIL import Image
from io import BytesIO
from StringIO import StringIO
#from pylab import nbytes

ap = argparse.ArgumentParser()
ap.add_argument("--url", type=str, default="pic")
ap.add_argument("--stats", action="store_true")
ap.add_argument("--showpic", action="store_true")
ap.add_argument("--showsize", action="store_true")
#ap.add_argument("--pctthresh", type=float, default=0.95)
args = vars(ap.parse_args())

# COMMANDS
    # >python client2.py --showpic --showsize
    # >python client2.py --url take5 --stats
    # >python client2.py --url take6 --stats --showpic --showsize

def get_image_bytes(img):
    img_file = BytesIO()
    img.save(img_file, 'png')
    return img_file.tell()

def convert_image(r):
    return np.array(Image.open(r.raw).convert('RGB'))

def convert_image2(r):
    return Image.open(StringIO(r.content))


def basic():
    
    t0 = time.time()
    
    url = 'http://10.0.0.109:5000/'
    url += args["url"]
    r = requests.get(url, stream=True)
    
    print 'time: ', str(time.time() - t0)
    
    if args["stats"]:
        try:
            print r.ok
            if r.ok:
                content_len = len(r.content)
                if content_len > 0:
                    print r.content[:min(content_len,100)]
        except:
            'there was no r.'

    if args["showsize"]:
        if not(r.ok):
            print 'r not okay.'
        else:
            try:   
                img_a = convert_image2(r)
                print 'bytes img_a: ', str(get_image_bytes(img_a))
                img_a2 = img_a.convert('RGB')
                print 'bytes img_a2: ', str(get_image_bytes(img_a))
            
            except Exception as e:
                print e.message

    if args["showpic"]:
        img_a  = convert_image2(r)
        plt.imshow(img_a)
        plt.show()
    
    

def mini_image():

    t00 = time.time()
    
    for i in range(8):
        for j in range(8):
    
            ij = str(i) + str(j)
            url = 'http://127.0.0.1:5000/pic_i/' + ij
            
            t0 = time.time()
            r = requests.get(url, stream=True)
            t1 = time.time()
            print 'time: ', str(t1 - t0)

            if ij == "11":
                pass
                #img = convert_image(r)
                #plt.imshow(img)
                #plt.show()



    print 'total time: ', str(time.time() - t00)

#mini_image()
basic()