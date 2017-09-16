import os, sys, time, copy, random, argparse
import traceback
import numpy as np
import cv2
import imutils
from collections import deque
from matplotlib import image as mpimg
from matplotlib import pyplot as plt


def load_images(dir_path,n = 1):
    #dir_path = "data/write/july/imgs17/"
    ext = ".jpg"
    n = 1
    img = []
    for pind in xrange(1,n+1):
        for ptype in ['img', 'img_t', 'rect', 'rect_t']:
            pic_and_path = dir_path
            pic_and_path += ptype
            pic_and_path += str(pind)
            pic_and_path += ext
            _img =  cv2.imread(pic_and_path)
            plt.imshow(cv2.cvtColor(_img, cv2.COLOR_BGR2RGB))
            #plt.imshow(_img)
            plt.show()
            img.append(_img)
    return img


def multi_hist(l_hists = [], full = True, bins = 50 ):
    
    h,w = (2,3) if full else (1,3) 
    f ,arrax = plt.subplots(h,w)
    for i in range(h*w):
        hi, wi = i / 3, i % 3
        print hi, ' ', wi
        if full:
            arrax[hi][wi].hist(l_hists[i], bins = bins)
        else:
            arrax[i].hist(l_hists[i], bins = bins)
        #arrax[i].set_title('color : '  + str(clr))
    f.subplots_adjust(hspace=1)
    plt.show()