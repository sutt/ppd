import random, time, os, sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.path as path
import matplotlib.animation as animation


def setup_hist(fig, ax, inp_bins = 100,**kwargs):
    
    #data = np.random.randn(1000)
    print 'inp_bins: ', inp_bins
    #data = map(lambda x: random.randint(0,10),range(1000))

    z = np.random.randn(100)
    u, var = 128, 30
    data = map(lambda z_i: u + (z_i*var), z)

    n, bins = np.histogram(data, inp_bins)

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

    #ax.set_xlim(left[0], right[-1])
    #ax.set_xlim(left[0] - 1, right[-1] + 1)
    x_lo, x_hi = kwargs.get('x_lo',-1), kwargs.get('x_hi',256)
    ax.set_xlim(x_lo, x_hi)
    
    if kwargs.get('y_hi',-1) == -1:
        y_lo, y_hi = 0 ,top.max()       #dyanmic sizing
    else:
        y_lo, y_hi = kwargs.get('y_lo',0), kwargs.get('y_hi',500)
    ax.set_ylim(y_lo, y_hi)
    

    hist_num = kwargs.get('hist_num',-1)
    if hist_num > -1 and hist_num < 3:
        ax.set_title('color: '+ list('bgr')[hist_num] )
        

    return ax, top, bottom, n, verts, patch


class LiveHist():

    def __init__(self, **kwargs):
        
        h, w = kwargs.get('h',1), kwargs.get('w',1)
        self.fig, self.ax = plt.subplots(h,w)

        self.bins = kwargs.get('bins',100)
        print 'this hist has num bins: ', str(self.bins)
        self.N = h*w
        
        N = self.N
        self.top =    [None]*N
        self.bottom = [None]*N
        self.n =      [None]*N
        self.verts =  [None]*N    
        self.patch =  [None]*N

        # SET GLOBALS FIRST TIME
        for h in range(self.N):
            
            if self.N > 1:
                inp_ax = self.ax[h]
            else:
                inp_ax = self.ax

            ret = setup_hist(self.fig 
                            ,inp_ax
                            ,inp_bins = self.bins
                            ,x_lo = kwargs.get('x_lo',-1)
                            ,x_hi = kwargs.get('x_hi',256)
                            ,y_lo = kwargs.get('y_lo',-1)
                            ,y_hi = kwargs.get('y_hi',-1)
                            ,hist_num = h
                            )
            
            if self.N > 1:
                self.ax[h] = ret[0]
            else:
                self.ax = ret[0]

            self.top[h] = ret[1]
            self.bottom[h] = ret[2]
            self.n[h] = ret[3]
            self.verts[h] = ret[4]
            self.patch[h] = ret[5]

    def set_xlim(self, x_lo, x_hi, **kwargs):
        ax_ind = kwargs.get('ax_ind',range(self.N) )
        for h in ax_ind:
            self.ax[h].set_xlim(x_lo,x_hi)

    def set_ylim(self, y_lo, y_hi, **kwargs):
        ax_ind = kwargs.get('ax_ind',range(self.N) )
        for h in ax_ind:
            self.ax[h].set_ylim(y_lo,y_hi)

    def get_figure_objects(self):
        return self.fig, self.ax

    def animate_j(self,j, inp_data):
        data = inp_data
        n, bins = np.histogram(data, self.bins)
        self.top[j] = self.bottom[j] + n
        self.verts[j][1::5, 1] = self.top[j]
        self.verts[j][2::5, 1] = self.top[j]
        return [self.patch[j], ]

    def animate_j_wrapper(self,i,j,inp_data): 
        return self.animate_j(j,inp_data)
    
    def show_plt(self,**kwargs):
        wait_time = kwargs.get('wait_time',5)
        print 'open for window moving for %f secs ...' % (wait_time)
        plt.show(False)
        plt.pause(wait_time)
        print 'finsihed with window moving time.'

    def clear_figure(self, **kwargs):
        plt.clf()
        #self.fig.clf()


    def update_figure(self, inp_data, ax_ind = range(3), **kwargs):
        
        frames = kwargs.get('frames', 1)
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
                                        #blit=True only updates 1 histo

            #wrong, inp_data is still not histo
            if kwargs.get('adapt_xlim',False):
                self.set_xlim( x_lo = 0, x_hi = inp_data[j].max(), ax_ind = (j,))
            if kwargs.get('adapt_ylim',False):
                self.set_xlim( y_lo = 0, y_hi = inp_data[j].max(), ax_ind = (j,))

            if kwargs.get('show',True):
                plt.show(False)
                plt.pause(pause_time)

    
    def end_class():
        pass
        
