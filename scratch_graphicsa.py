import matplotlib.pyplot as plt
import time, random
import matplotlib.patches as patches
import matplotlib.path as path
import matplotlib.animation as animation
import numpy as np
from GraphicsA import LiveHist


def mock_gaussian(n = 100, **kwargs ):
    z = np.random.randn(n)
    u, var = kwargs.get('u',0), kwargs.get('var',1)
    return map(lambda z_i: u + (z_i*var), z)
    
def rand_gauss_params():
    u = random.randint(0,255)
    var = random.randint(10,50)
    return u, var

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

run_type = 'mockcolor'

if run_type == 'simple':
    N = 1
    lh_0 = LiveHist(h=1,w=N, bins = 11, x_lo = -1, x_hi = 11)
elif run_type == 'basic':
    N = 3
    lh_0 = LiveHist(h=1,w=N, bins = 11, x_lo = -1, x_hi = 11)
elif run_type == 'mockcolor':
    N = 3
    lh_0 = LiveHist(h=1,w=N, bins = 30, x_lo = -1, x_hi = 256)


lh_0.show_plt(wait_time = 2)        #Allow it to resize
time.sleep(0.5)                     #LET IT LOAD
tic = time.time()


for i in range(100):

    u, var = rand_gauss_params()
    data = map( lambda x: mock_gaussian(n=100,u=u,var=var), range(N) )

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