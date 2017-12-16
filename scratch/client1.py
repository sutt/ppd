from matplotlib import pyplot as plt
import os, sys, time
import cv2
import requests
from PIL import Image
import numpy as np
from pylab import nbytes
from io import BytesIO

ip = "10.0.0.109"
#ip = "127.0.0.1"
sub = "take4"

def get_image_bytes(img):
    img_file = BytesIO()
    img.save(img_file, 'png')
    return img_file.tell()

def convert_image(r):
    return np.array(Image.open(r.raw).convert('RGB'))

def full_image():
    
    t0 = time.time()
    url = 'http://' + ip + ':5000/' + sub +'/'
    
    try:
        r = requests.get(url, stream=True, timeout = 8.0)
    except:
        print 'nah'
    t1 = time.time()
    print 'time: ', str(t1 - t0)
    print r.ok
    
    if False and r.ok:
        
        t0 = time.time()

        img_a = Image.open(r.raw)
        print 'bytes img_a: ', str(get_image_bytes(img_a))

        img_a2 = img_a.convert('RGB')
        print 'bytes img_a2: ', str(get_image_bytes(img_a))

        img_b = np.array(img_a2)
        print 'img_b shape: ', str(img_b.shape)

        my_size = sys.getsizeof(img_b)
        print 'getsizeof img_b: ', str(my_size)
        #print 'bytes img_b: ', str(get_image_bytes(img_b))
        t1 = time.time()
        print 'time: ', str(t1-t0)

        plt.imshow(img_a)
        plt.show()
        time.sleep(2)
        plt.close()

def mini_image():

    t00 = time.time()
    
    for i in range(8):
        for j in range(8):
    
            ij = str(i) + str(j)
            url = 'http://' + ip + ':5000/pic_i/' + ij
            
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