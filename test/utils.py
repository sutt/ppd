import os, sys, time, datetime
import numpy as np
import cv2
import pandas as pd

sys.path.append("../")
from modules.ImgUtils import binary_diff

''' 

RECIPE:
    use this recipe during debug to capture benchmark-data / stub-data 
    for use in displayclass tests:

    >pathfn = "data/test/guiview/displayclass/scratch/stubframe.png" #write to scratch-dir
    >stubframe = display.getOrigFrame()                         #from guiview context
    >cv2.imwrite(pathfn, stubframe)                             #should print "True"

    for bench data:
    >bench_data = display.frame
    >bench_data.size            #to validate it exists

'''

def verifyAction(msg="press Y to continue; N to exit\n", prefix=""):
    ''' allow user input to cancel next action '''
    
    display_message = prefix + " \n" + msg
    
    ret = raw_input(display_message)
    
    if ret.capitalize() == "Y":
        print 'proceeding...'
        return False
    else:
        print 'exiting the current function...'
        return True


class ImgDiff:

    ''' Helper class for comparing images. 
            (when running asserts, this can perform the check and 
             output diffs to a log directory. This allows pytest 
             to stop on the assert in question while still running
             a detailed diff here.)
    '''
    
    def __init__(self, log_path = None):
        
        self.log_output_path = log_path
        self.bLog = (log_path is not None)
        


    def diffImgs(self, imgBenchmark, imgTest, **kwargs):

        bAssert = self.diff_imgs(imgBenchmark, imgTest)

        if not(bAssert) and not(kwargs.get('noLog', False)):
            try:
                
                self.summarize_diff_imgs(imgBenchmark, imgTest)
                
                if self.bLog:

                    img = self.viz_diff_imgs(imgBenchmark, imgTest)
                    
                    fn = str(datetime.datetime.now())
                    fn = fn.replace(" ", "-").replace(".", "-").replace(":", "-")
                    fn += ".png"
                    
                    pathfn = os.path.join(self.log_output_path, fn)

                    ret = cv2.imwrite(pathfn, img)

                    if ret:
                        print 'logged out success to: ', fn

            except:
                print 'failed to output diff to test log'

        return bAssert
    
    @staticmethod
    def diff_imgs(imgBenchmark, imgTest):
        ''' return True if images perfectly match, False otherwise'''
        try:
            frame_diff = cv2.absdiff(imgBenchmark, imgTest)
            return (sum(sum(sum(frame_diff))) == 0)
            #maybe do an all() instead?
        except:
            return False

    @staticmethod
    def summarize_diff_imgs(imgBenchmark, imgTest, n_diffs = 10):
        ''' when images are different, call this to see how different. '''
        
        try:
            assert imgBenchmark.shape == imgTest.shape
        except:
            print 'imgs not same size. '
            print '      imgBenchmark: %s' % str(imgBenchmark.shape)
            print '      imgTest     : %s'% str(imgTest.shape)
            return 
        
        try:
            #TODO - for grayscale vs rgb
            frame_diff = cv2.absdiff(imgBenchmark, imgTest)
            print 'total pix diff: ',  str(sum(sum(sum(frame_diff))))
        except:
            print 'couldnt perform a pix diff'

        try:
            frame_diff = cv2.absdiff(imgBenchmark, imgTest)
            #TODO - implement this; where are pix dif?
        except:
            print 'couldnt print out diff pix index'

        try:
            assert imgBenchmark.dtype.name == imgTest.dtype.name
        except:
            print 'imgs not the same dtype. '
            print '      imgBenchmark: %s' % str(imgBenchmark.dtype.name)
            print '      imgTest     : %s'% str(imgTest.dtype.name)
            

    @staticmethod
    def viz_diff_imgs(imgBenchmark, imgTest, b_gray=True):
        ''' when images are different, call this to visually see how different.
            helpful for when, e.g. just annotation has changed '''
        
        if b_gray:
            _a = cv2.cvtColor(imgBenchmark, cv2.COLOR_BGR2GRAY)
            _b = cv2.cvtColor(imgTest, cv2.COLOR_BGR2GRAY)    
            imgDiff = cv2.absdiff(_a, _b)
            
            imgDiff_3ch = cv2.cvtColor(imgDiff, cv2.COLOR_GRAY2BGR)
            
        else:
            imgDiff_3ch = cv2.absdiff(imgBenchmark, imgTest)

        diffOutput = binary_diff(imgDiff_3ch)
    
        #TODO - better function here, include non-same size imgs
        output = np.concatenate((imgBenchmark, imgTest, diffOutput), axis=0)

        return output
        

def diff_pd(df1, df2):
    '''
    Identify differences between two pandas DataFrames
    https://stackoverflow.com/questions/17095101/outputting-difference-in-two-pandas-dataframes-side-by-side-highlighting-the-d
    '''
    assert (df1.columns == df2.columns).all(), \
        "DataFrame column names are different"
    if any(df1.dtypes != df2.dtypes):
        "Data Types are different, trying to convert"
        df2 = df2.astype(df1.dtypes)
    if df1.equals(df2):
        print 'they are the same according to diff_pd'
        return None
    else:
        # need to account for np.nan != np.nan returning True
        diff_mask = (df1 != df2) & ~(df1.isnull() & df2.isnull())
        ne_stacked = diff_mask.stack()
        changed = ne_stacked[ne_stacked]
        changed.index.names = ['id', 'col']
        difference_locations = np.where(diff_mask)
        changed_from = df1.values[difference_locations]
        changed_to = df2.values[difference_locations]
        return pd.DataFrame({'from': changed_from, 'to': changed_to},
                            index=changed.index)

def listContainSameElems(list1, list2):
    ''' return True if elements contain same elements, False otherwise'''
    b1 = all(map(lambda x: x in list2, list1))
    b2 = all(map(lambda x: x in list1, list2))
    return (b1 and b2)


# if __name__ == "__main__":

TEST_DATA_DIR = "../data/test/helpers/utils_tests/"

def test_listContainsSameElems():

    a1, a2 = [1,2], [2,1]
    assert listContainSameElems(a1, a2) == True

    a1, a2 = [1,2], [2,0]
    assert listContainSameElems(a1, a2) == False

    a1, a2 = [1,2,3], [2,1,0]
    assert listContainSameElems(a1, a2) == False

    a1, a2 = [1,2], [1,2.0]
    assert listContainSameElems(a1, a2) == True

def test_diff_imgs_1():
    ''' test img_diff works for TruePositives and TrueNegatives '''
    
    img1 = cv2.imread(os.path.join(TEST_DATA_DIR, "stubframe.png"))
    img1copy = cv2.imread(os.path.join(TEST_DATA_DIR, "stubframe.png"))
    img2 = cv2.imread(os.path.join(TEST_DATA_DIR, "bench_yes_score.png"))

    diff = ImgDiff()

    #True Positives
    assert diff.diff_imgs(img1, img1copy)
    assert diff.diff_imgs(img1, img1)
    assert diff.diffImgs(img1, img1copy)

    #True Negatives
    assert diff.diffImgs(img1, img2) == False
    assert diff.diff_imgs(img1, img2) == False


def test_summarize_diff_imgs_1():
    ''' use the same methods as the function to verify answer matches a benchmark '''
    
    diff = ImgDiff(TEST_DATA_DIR)
    
    #test pixel diff - actual images
    img1 = cv2.imread(os.path.join(TEST_DATA_DIR, "stubframe.png"))
    img2 = cv2.imread(os.path.join(TEST_DATA_DIR, "bench_yes_score.png"))

    frame_diff = cv2.absdiff(img1, img2)
    assert sum(sum(sum(frame_diff))) == 575
    
    #test dif sizes - synthetic images
    img3a = np.zeros(shape=(480,640, 3))
    img4a = np.zeros(shape=(100,200, 3))
    img3b = np.zeros(shape=(480,640, 3))
    img4b = np.zeros(shape=(480,640))

    assert (img3a.shape == img4a.shape) == False
    assert (img3b.shape == img4b.shape) == False


def test_viz_diff_imgs_1():
    ''' test the output of a visual diff matches what's expected '''
    
    img1 = cv2.imread(os.path.join(TEST_DATA_DIR, "stubframe.png"))
    img2 = cv2.imread(os.path.join(TEST_DATA_DIR, "bench_yes_score.png"))
    
    benchmark_diff_1 = cv2.imread(os.path.join(TEST_DATA_DIR, "benchmarkDiff1.png"))

    files0 = os.listdir(TEST_DATA_DIR)
    
    diff = ImgDiff(log_path = TEST_DATA_DIR)

    diff.diffImgs(img1, img2)   #should be False, therefore will output a viz_diff log

    files1 = os.listdir(TEST_DATA_DIR)
    newfiles = filter(lambda f: f not in files0, files1)
    log_fn = newfiles[0]
    log_img = cv2.imread(os.path.join(TEST_DATA_DIR, log_fn))

    assert diff.diff_imgs(benchmark_diff_1, log_img)        # main test
    
    try:
        for f in newfiles:
            os.remove(os.path.join(TEST_DATA_DIR, f))       # cleanup
    except:
        print 'couldnt cleanup up files in test_viz_diff_1()'


# if __name__ == "__main__":
#     verifyAction()
#     print 'continued..'