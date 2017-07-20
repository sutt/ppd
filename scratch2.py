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

print 'BACKEDN: ', plt.get_backend()


#Setup, unnec so far for simple

#simple
#plt.hist([1])
#plt.ion()
#plt.show()

h,w = 1,3
f ,arrax = plt.subplots(h,w)


for i in range(10):

    sample_i = map(lambda x: random.uniform(0,10),range(7))
    
    #Do a simple plot live
    plt.hist(sample_i)
    plt.draw()
    plt.pause(0.01)
    plt.gcf().clear()
    
    #Do a multiplot live
    # dhistos = {}
    # for j in list('bgr'):
    #     dhistos[str(j)] = sample_i
    # print histos
    # multi_hist_live(f, arrax, d_hists=dhistos, horiz=True)
    
    #other commands not used
    #ion()
    #plt.show(block=False)
    

#plt.show()