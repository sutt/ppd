
#from sg_imp import *
import sg_imp

from sg_sub import sub1

def main():
    #print 'before init: ', var1
    
    print 'before init1: ', sg_imp.var1
    print 'before init1, var2: ', sg_imp.var2

    sg_imp.init()

    print 'after init1: ', sg_imp.var1
    print 'after init1, var2: ', sg_imp.var2

    # init2()
    # #print 'after init2: ', var1
    # sub1()
    # print 'after sub1: ', var1
    # var1 = 2
    # print 'after main set: ', var1
    # sub1()
    # print 'after sub1 again: ', var1


main()