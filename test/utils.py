import os, sys, time
import cv2


''' 

TODO:
    [ ] finish imgdiff
        [ ] copy funcs from book
    [ ] test with a failed test


RECIPE:
    use this recipe during debug to capture benchmark-data / stub-data 
    for use in displayclass tests:

    >pathfn = "data/test/guiview/display/scratch/stubframe.png" #write to scratch-dir
    >stubframe = display.getOrigFrame()                         #from guiview context
    >cv2.imwrite(stubframe, pathfn)                             #should print "True"

    for bench data:
    >bench_data = display.frame
    >bench_data.size            #to validate it exists



'''
    

class ImgDiff:

    ''' Helper class for comparing images. 
            (when running asserts, this can perform the check and 
             output diffs to a log directory. This allows pytest 
             to stop on the assert in question while still running
             a detailed diff here.)
    '''
    
    def __init__(self):
        self.log_output_path = ""
        self.bLog = False

    def write_log(self, data, _type="viz"):
        ''' output a file that explains diffs '''
        pass


    @classmethod
    def diffImgs(cls, imgBenchmark, imgTest, **kwargs):

        bAssert = cls.diff_imgs(imgBenchmark, imgTest)

        if not(bAssert):
            try:
                #TODO - need a path to directory for holding logs
                #TODO - need a way to name file
                cls.summarize_diff_imgs(imgBenchmark, imgTest)
                # cls.display_diff_imgs(imgBenchmark, imgTest)
            except:
                print 'failed to output diff to test log'

        return bAssert
    
    @staticmethod
    def diff_imgs(imgBenchmark, imgTest):
        ''' return True if images perfectly match, Fale otherwise'''
        #TODO this is for 3-color imgs
        #TODO - make these asserts
        print imgBenchmark.size
        print imgTest.size
        frame_diff = cv2.absdiff(imgBenchmark, imgTest)
        print frame_diff.shape
        cv2.imshow('tada', imgTest)
        key = cv2.waitKey(1) & 0xFF
        time.sleep(10)

        return (sum(sum(sum(frame_diff))) == 0)

    @staticmethod
    def summarize_diff_imgs(imgBenchmark, imgTest):
        ''' when images are different, call this to see how different. '''
        pass
        #TODO - are dims the same?
        #TODO - how many pixels are diff?
        frame_diff = cv2.absdiff(imgBenchmark, imgTest)
        out = sum(sum(sum(frame_diff)))
        print 'total pix diff: ',  str(out)


    @staticmethod
    def display_diff_imgs(imgBenchmark, imgTest, b_show_diff=True):
        ''' when images are different, call this to visually see how different.
            helpful for when, e.g. just annotation has changed '''
        pass
        #TODO - concantenate imgs above and below
        #TODO - add diff