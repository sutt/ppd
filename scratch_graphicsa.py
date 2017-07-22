import matplotlib.pyplot as plt
import time, random
import matplotlib.patches as patches
import matplotlib.path as path
import matplotlib.animation as animation
import numpy as np
from GraphicsA import LiveHist


def mock_color(n = 100, b_as_numpy = False ):
    data = np.random.randn(n)
    if not(b_as_numpy):
        return data
    else:
        return np.array(data)

def mock_integer(n = 100, a=0,b=10):
    return map(lambda x: random.randint(0,10),range(n))
                
def mock_bivariate(n1 = 25, n2 = 10,a = 0, b = 10 ):
    data = []
    for xx in range(3):
        d = random.randint(a,b)
        d2 = random.randint(a,b)
        dd = [d] * n1
        dd2 = [d2] * n2
        dd3 = dd[:]
        dd3.extend(dd2[:])
        data.append( np.array(  dd3 ) )
    return data

N = 1
lh_0 = LiveHist(h=1,w=1, bins = 11, x_lo = -1, x_hi = 11)

#lh_0.show_plt()        #Allow it to resize
time.sleep(0.5)         #LET IT LOAD
tic = time.time()


for i in range(100):

    data = map( lambda x: mock_integer( n = 50 * i), range(N) )

    for h in range(len(data)):
        print data[h][:min(5,len(data[h]))]
    
    lh_0.update_figure( data
                        ,ax_ind = range(N)
                        ,frames = 1
                        ,show = True
                        ,epsilon = .0001)
    
    print 'DONE ', str(i)

    if i == 5:
        #lh_0.set_xlim(-10,20)
        pass

print 'time: ', str(time.time() - tic)

time.sleep(4)

# so we need to call plt.show() from main thread? 
    # no, just show(False); pause(t);