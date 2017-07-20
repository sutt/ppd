import os, sys, time, copy
import traceback
import numpy as np
import cv2
import imutils
from collections import deque
from matplotlib import image as mpimg
from matplotlib.pyplot import ion
import random

from matplotlib import pyplot as plt

from track_a import *

#plt.hist([1])
#plt.ion()
#plt.show()
h,w = 1,3
f ,arrax = plt.subplots(h,w)

for i in range(10):

    sample_i = map(lambda x: random.uniform(0,10),range(7))
    histos = {}
    for j in list('bgr'):
        histos[str(j)] = sample_i
    print histos
    multi_hist_live(f, arrax, d_hists=histos, horiz=True)
    #ion()
    #plt.hist([1])
    # plt.hist(sample_i)
    # plt.draw()
    # plt.pause(0.01)
    # plt.gcf().clear()
    #plt.show()
    #plt.show(block=False)
    #time.sleep(1)
    #plt.show(block=False)

#plt.show()