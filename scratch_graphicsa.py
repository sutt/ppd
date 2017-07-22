import matplotlib.pyplot as plt
import time
import matplotlib.patches as patches
import matplotlib.path as path
import matplotlib.animation as animation
from GraphicsA import LiveHist

lh_0 = LiveHist(h=1,w=3)
print lh_0.N

# print 'start with resize time'
# lh_0.show_plt()
# print 'done with resize time'

#print 'update once'
#lh_0.update_figure(1, ax_ind = range(3), frames = 1, show = True)
#time.sleep(3)
#print 'done with resize'
# plt.show(False)
# plt.pause(0.1)
# for i in range(4):
#     time.sleep(4)
#     print i

#LET IT LOAD
time.sleep(0.5)
print 'GOING IN...'

tic = time.time()
for i in range(10):
    
    lh_0.update_figure( (1,1,1)
                        ,ax_ind = range(3)
                        ,frames = 1
                        ,show = True
                        ,epsilon = .0001)
    
    print 'DONE ', str(i)

print 'time: ', str(time.time() - tic)

# print 'resize 2'
# time.sleep(1)
# print 'end resize 2'

# for i in range(10):
    
#     # frames = 1
#     # ani = animation.FuncAnimation(lh_0.fig
#     #                                 ,lh_0.animate_j_wrapper 
#     #                                 ,frames = frames
#     #                                 ,repeat=False
#     #                                 ,interval = 100
#     #                                 ,blit=False)
    
#     ret = lh_0.update_figure(1, ax_ind = range(3), frames = 1)
#     #time.sleep(0.3)
#     print 'DONE ', str(i)
    
#     # plt.show(False)
#     # plt.pause(0.1)
# time.sleep(2)
# #plt.show(True)
# print 'ENDING:...'
# lh_0 = None
# time.sleep(3)
# print 'out'

#so we need to call plt.show() from main thread?