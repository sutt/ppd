from array import *

arr = {1,2,3}

for i in arr:
    print i

n = 5

arr2 = array('i',(0,)*n)
arr2[3] = 17
print arr2
print len(arr2)


arr3 = [None]*n
arr3[3] = 17
print arr3
print len(arr3)

