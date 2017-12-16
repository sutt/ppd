from matplotlib import pyplot as plt
import cv2
import os, sys, time
import requests
from PIL import Image
from io import BytesIO
import numpy as np
from StringIO import StringIO
#from pylab import nbytes


def get_image_bytes(img):
    img_file = BytesIO()
    img.save(img_file, 'png')
    return img_file.tell()

def convert_image(r):
    return np.array(Image.open(r.raw).convert('RGB'))

def full_image():
    t0 = time.time()
    
    url = 'http://10.0.0.109:5000/takeverysimple/'
    r = requests.get(url, stream=True)
    
    t1 = time.time()
    print 'time: ', str(t1 - t0)
    
    try:
        print r.ok
        if r.ok:
            print r.content[:100]
    except:
        'there was no r.'

    if True:
        #img = convert_image(r)
        img_a  = Image.open(StringIO(r.content))
        plt.imshow(img_a)
        plt.show()
    
    try:
        img_a = Image.open(r.raw)
        #print 'bytes img_a: ', str(get_image_bytes(img_a))

        #img_a2 = img_a.convert('RGB')
        #print 'bytes img_a2: ', str(get_image_bytes(img_a))
    
    except Exception as e:
        print e.message

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
full_image()