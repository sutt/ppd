import os, sys
import cv2
import argparse
from vidwriter import VidWriter

'''
    Script to re-write a vid, without particular frames:

        >python deleteframe.py --file x/x/vid.avi --delframes 1,2
        
            ->outputs: x/x/vid_del.avi  (without frames 1 and 2 (index-0))

            use: --fourcc 0   (for lossless)

    note: still have to delete these frames manually from timelog, metalog
'''

def main(vidPathFn, removeFrameInds, frameSize=None, fourcc=None):
    
    outputDir, vidFn = os.path.split(vidPathFn)    
    
    writeVidFn = ( os.path.splitext(vidFn)[0] 
                 + "_del" 
                 + os.path.splitext(vidFn)[1])

    cam = cv2.VideoCapture(vidPathFn)
    
    if not(cam.isOpened()):
        print 'failed to load vid; exiting'
        sys.exit()
    
    vidwriter = None

    frameCounter = -1

    while(cam.isOpened()):

        ret, frame = cam.read()

        if ret:

            #on 1st frame create writer ---------
            if vidwriter is None:

                if fourcc is None:
                    fourcc = "h264"

                if frameSize is None:
                    frameSize = frame.shape[:2][::-1]

                try:
                    vidwriter = VidWriter( 
                                savefn = os.path.join(outputDir, writeVidFn)
                                ,fourcc = fourcc
                                ,outshape = frameSize
                                )
                except:
                    print 'failed to create vidwriter; exiting'
                #-----------------------------------

            frameCounter += 1

            if frameCounter not in removeFrameInds:

                vidwriter.write(frame)
        
        else:
            break

    print 'done; new video: ', str(os.path.join(outputDir, writeVidFn))



def countFrames(vidPathFn):
    ''' helper for test '''
    cam = cv2.VideoCapture(vidPathFn)
    frameCounter = 0
    try:
        while(cam.isOpened()):
            ret, frame = cam.read()
            if ret:
                frameCounter +=1
            else:
                break
    except:
        return frameCounter
    return frameCounter

def test_deleteframe_1():
    ''' test deleting 1 frame '''

    TEST_DATA_PATH = "data/test/deleteframe/simple/"
    TEST_VID_FN = "frames5.avi"
    TEST_OUT_FN = "frames5_del.avi"

    #setup
    if TEST_OUT_FN in os.listdir(TEST_DATA_PATH):
        try:
            os.remove(TEST_DATA_PATH + TEST_OUT_FN)
        except:
            print 'couldnt delete video file'
            assert False

    main(TEST_DATA_PATH + TEST_VID_FN, (0,))

    assert countFrames(TEST_DATA_PATH + TEST_VID_FN) == 5

    assert countFrames(TEST_DATA_PATH + TEST_OUT_FN) == 4


def test_deleteframe_2():
    ''' test deleting multi frames on a 1080p vid '''

    TEST_DATA_PATH = "data/test/deleteframe/multi/"
    TEST_VID_FN = "frames5_1080.avi"
    TEST_OUT_FN = "frames5_1080_del.avi"

    #setup
    if TEST_OUT_FN in os.listdir(TEST_DATA_PATH):
        try:
            os.remove(TEST_DATA_PATH + TEST_OUT_FN)
        except:
            print 'couldnt delete video file'
            assert False

    main(TEST_DATA_PATH + TEST_VID_FN, (0,1,2))

    assert countFrames(TEST_DATA_PATH + TEST_VID_FN) == 5

    assert countFrames(TEST_DATA_PATH + TEST_OUT_FN) == 2


def parseDelFrames(strInput):
    
    output = []
    
    listNums = strInput.split(",")
    
    for elem in listNums:
        try:
            _num = int(elem)
            output.append(_num)
        except:
            #couldn't convert to int
            pass
    
    return tuple(output)

def parseFrameSize(strInput):
    listNums = strInput.split(",")
    if len(listNums) != 2:
        print 'failed to parse frameSize; exiting'
        sys.exit()
    


if __name__ == "__main__":

    ap = argparse.ArgumentParser()
    ap.add_argument("--file", type=str, default="")
    ap.add_argument("--delframes", type=str, default="")
    ap.add_argument("--framesize", type=str, default="")
    ap.add_argument("--fourcc", type=str, default="")
    args = vars(ap.parse_args())
    
    
    if args["file"] == "":
        print 'need to include --file'
    else:
        vidPathFn = args["file"]

    if args["delframes"] == "":
        print 'need to include --delframes'
        sys.exit()
    else:
        removeFrameInds = parseDelFrames(args["delframes"])

    if args["fourcc"] == "":
        fourcc = None
    elif args["fourcc"] == "0":
        fourcc = 0      #needs to be int for lossless
    else:
        fourcc = args["fourcc"]

    if args["framesize"] == "":
        frameSize = None
    else:
        frameSize = parseFrameSize(args["framesize"])


    main( vidPathFn = vidPathFn
        ,removeFrameInds = removeFrameInds
        ,fourcc = fourcc
        ,frameSize = frameSize
        )


