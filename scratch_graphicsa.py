import matplotlib.pyplot as plt
import time
import matplotlib.patches as patches
import matplotlib.path as path
import matplotlib.animation as animation
from GraphicsA import LiveHist

lh_0 = LiveHist(h=1,w=3)
print lh_0.N

plt.show(False)

time.sleep(2)
print 'GOING IN...'

for i in range(100):
    
    frames = 10
    ani = animation.FuncAnimation(lh_0.fig
                                    ,lh_0.animate_j_wrapper 
                                    ,frames = frames
                                    ,repeat=False
                                    ,interval = 100
                                    ,blit=False)
    #ret = lh_0.update_figure(1, ax_ind = range(3), frames = 10)
    
    print 'DONE ', str(i)
    
    plt.show(False)
    plt.pause(0.1)
    # time.sleep(0.1)
    #plt.show()
    #lh_0.get_figure_objects()[0].show(False)

print 'at the end'
time.sleep(2)
#plt.show(True)

#so we need to call plt.show() from main thread?