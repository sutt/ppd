import cv2
import numpy as np
import os,sys

from ImgUtils import px3clr_3px1clr as three_color
from ImgUtils import px_to_list

#import os
#os.chdir('c:/users/wsutt/desktop/files/ppd/ppd/')

def main():
    
    p = "data/write/july/imgs17/img1.jpg"
    img = cv2.imread(p)

    print 'len of img: %i' % len(img)

    t1 = px_to_list(img)
    t2 = three_color(t1)

    print 'len of t1: %i' % len(t1)
    print 'len of t2: %i' % len(t2)
    print 'len of t2[0]: %i' % len(t2[0])

    return img

if __name__ == "__main__":
    main()