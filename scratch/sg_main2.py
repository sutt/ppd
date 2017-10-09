#import sg_imp
from sg_imp import var1, var2
from sg_imp import init

#from sg_imp import *
from sg_sub import sub1

print 'top of func: ', var1

def main():
    # var1 = sg_imp.var1
    # var2 = sg_imp.var2
    global var1
    global var2
    

    print 'before init1: ', var1
    print 'before init1, var2: ', var2

    init()

    print 'after init1: ', var1
    print 'after init1, var2: ', var2

    sub1()

    print 'after sub1: ', var1
    print 'after sub1, var2: ', var2
    
    var1 = 4
    var2 = 4
    print 'after main set: ', var1
    print 'after main set, var2: ', var2

    sub1()
    print 'after sub1 again: ', var1
    print 'after sub1 again, var2: ', var2


main()