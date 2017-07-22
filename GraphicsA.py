import random, time, os, sys

import numpy as np

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.path as path
import matplotlib.animation as animation


def setup_hist(fig, ax, **kwargs):
    
    data = np.random.randn(1000)
    n, bins = np.histogram(data, 100)

    left = np.array(bins[:-1])
    right = np.array(bins[1:])
    bottom = np.zeros(len(left))
    top = bottom + n
    nrects = len(left)

    nverts = nrects*(1 + 3 + 1)
    verts = np.zeros((nverts, 2))
    codes = np.ones(nverts, int) * path.Path.LINETO
    codes[0::5] = path.Path.MOVETO
    codes[4::5] = path.Path.CLOSEPOLY
    verts[0::5, 0] = left
    verts[0::5, 1] = bottom
    verts[1::5, 0] = left
    verts[1::5, 1] = top
    verts[2::5, 0] = right
    verts[2::5, 1] = top
    verts[3::5, 0] = right
    verts[3::5, 1] = bottom

    barpath = path.Path(verts, codes)
    patch = patches.PathPatch(
        barpath, facecolor='green', edgecolor='yellow', alpha=0.5)
    ax.add_patch(patch)

    ax.set_xlim(left[0], right[-1])
    ax.set_ylim(bottom.min(), top.max())

    return ax, top, bottom, n, verts, patch


class LiveHist():

    def __init__(self, **kwargs):
        
        h, w = kwargs.get('h',1), kwargs.get('w',1)
        self.fig, self.ax = plt.subplots(h,w)

        self.N = h*w
        
        N = self.N
        self.top = [None]*N
        self.bottom = [None]*N
        self.n = [None]*N
        self.verts =  [None]*N
        
        self.patch =  [None]*N

        # SET GLOBALS FIRST TIME
        for h in range(self.N):
            ret = setup_hist(self.fig,self.ax[h])
            self.ax[h] = ret[0]
            self.top[h] = ret[1]
            self.bottom[h] = ret[2]
            self.n[h] = ret[3]
            self.verts[h] = ret[4]
            self.patch[h] = ret[5]

    def get_figure_objects(self):
        return self.fig, self.ax

    def animate_j(self,j, inp_data):
        data = np.random.randn(1000)
        n, bins = np.histogram(data, 100)
        self.top[j] = self.bottom[j] + n
        self.verts[j][1::5, 1] = self.top[j]
        self.verts[j][2::5, 1] = self.top[j]
        return [self.patch[j], ]

    def animate_j_wrapper(self,i,j,inp_data): 
        return self.animate_j(j,inp_data)
    
    def show_plt(self,**kwargs):
        print 'a'
        plt.show(False)
        plt.pause(5)
        print 'b'

    def update_figure(self, inp_data, ax_ind = range(3), **kwargs):
        
        frames = kwargs.get('frames', 100)
        pause_time = kwargs.get('epsilon', 0.03)

        for j in ax_ind:
            ani = animation.FuncAnimation(self.fig
                                        ,self.animate_j_wrapper 
                                        ,frames = frames
                                        ,fargs = (j,inp_data[j])
                                        ,repeat=False
                                        ,blit=False) 
                                        #,interval = 1
                                        #save_count = 1 ? to preserve on blit 

            if kwargs.get('show',True):
                plt.show(False)
                plt.pause(pause_time)
        
        
 #blit=True only updates 1 histo