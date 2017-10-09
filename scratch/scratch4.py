"""
==================
Animated histogram
==================

This example shows how to use a path patch to draw a bunch of
rectangles for an animated histogram.

"""
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.path as path
import matplotlib.animation as animation

import random, time

def setup_fig(**kwargs):
    fig, ax = plt.subplots(1,kwargs.get('j', 1))
    return fig, ax

def setup_hist(fig, ax,):
    #fig, ax = plt.subplots(1,3)

    # histogram our data with numpy
    data = np.random.randn(1000)
    n, bins = np.histogram(data, 100)

    # get the corners of the rectangles for the histogram
    left = np.array(bins[:-1])
    right = np.array(bins[1:])
    bottom = np.zeros(len(left))
    top = bottom + n
    nrects = len(left)

    # here comes the tricky part -- we have to set up the vertex and path
    # codes arrays using moveto, lineto and closepoly

    # for each rect: 1 for the MOVETO, 3 for the LINETO, 1 for the
    # CLOSEPOLY; the vert for the closepoly is ignored but we still need
    # it to keep the codes aligned with the vertices
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


def main():
    
    def animate_j(j):
            # simulate new data coming in
        data = np.random.randn(1000)
        n, bins = np.histogram(data, 100)
        top[j] = bottom[j] + n
        verts[j][1::5, 1] = top[j]
        verts[j][2::5, 1] = top[j]
        return [patch[j], ]

    N = 3
    fig, ax = setup_fig(j = N)
    data = []
    
    print 'SHOW THAT WE ONLY COME THRU HERE ONCE.'    
    
    # INIT GLOBALS
    top = [None]*N
    bottom = [None]*N
    n = [None]*N
    verts =  [None]*N
    patch =  [None]*N

    # SET GLOBALS FIRST TIME
    for h in range(N):
        ret = setup_hist(fig,ax[h])
        ax[h] = ret[0]
        top[h] = ret[1]
        bottom[h] = ret[2]
        n[h] = ret[3]
        verts[h] = ret[4]
        patch[h] = ret[5]

    
    def animate_j_wrapper(i,fargs):
        j = random.randint(0,N-1)
        return animate_j(j)

    
    print 'GOING INTO LOOP'


    inp = 1
    ani = animation.FuncAnimation(fig, animate_j_wrapper 
                                    ,100
                                    , repeat=False, blit=True)
    
    plt.show(False)  #neccesary for showing changes

    print 'DONE, RETURNING FROM MAIN'
    return ani

if __name__ == "__main__":
    main()
    #plt.show(False)
    time.sleep(5)
    #plt.show()
    