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

#from example
import matplotlib.patches as patches
import matplotlib.path as path
import matplotlib.animation as animation

from scratch4 import *


print 'BACKEDN: ', plt.get_backend()


#Setup, unnec so far for simple

#simple
#plt.hist([1])
#plt.ion()
#plt.show()

def histof(arrax, d_hists):
    for i,clr in enumerate('bgr'):
        arrax[i].hist(d_hists[clr])
        #arrax[i].set_title('color : '  + str(clr))
    return arrax

def sample_data():
    dhistos = {}
    sample_i = map(lambda x: random.uniform(0,10),range(7))
    for j in list('bgr'):
            dhistos[str(j)] = sample_i
    return dhistos

h,w = 1,3
farrax = plt.subplots(h,w)
f ,arrax = farrax[0], farrax[1]
#f.subplots_adjust(hspace=1)

arrax = histof(arrax,sample_data())
plt.show(False)
plt.draw()

#StackOverflowMethod
#background = f.canvas.copy_from_bbox(arrax.bbox)
#points = histof(arrax, sample_data())

for i in range(10):

    
    #Do a simple plot live
    # plt.hist(sample_i)
    # plt.draw()
    # plt.pause(0.01)
    # plt.gcf().clear()
    
    #StackOverflowMethod
    #points.set_data(sample_data())
    #f.canvas.restore_region(background)
    #arrax.draw_artist(points)
    #f.canvas.blit(arrax.bbox)

    #arrax.cla()
    for i in range(3):
        arrax[i].cla()
    # farrax.cla()
    farrax[1] = histof(farrax[1],sample_data())
    #farrax.draw()
    # for i in range(3):
    #     arrax[i].draw()
    plt.draw()

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