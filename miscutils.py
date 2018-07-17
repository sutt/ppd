import os

def uniqueFn(fn_base
            ,fn_dir = None
            ,fn_ext = None
            ,method = "increment"
            ,guid_digits = 6
            ):
    ''' 
        Return a unique fn. Starts at fn_base1.ext.

        fn_base:    fn's base name  
                    different fn_base start back at fn_base1.ext
        fn_dir:     path to directory
                    (if None, uses current dir)
        fn_ext:     the extension
                    (NOT IMPLEMENTED if None, considers all fns in dir w/o ext)
        method:     str - "increment" or "guid"
        guid_digits:int - number of chars in guid
    '''

    if method == "increment":
        
        i = 0
        _dir = os.getcwd() if fn_dir is None else fn_dir
        files = os.listdir(_dir)
        
        while(True):
            i += 1
            fn = str(fn_base) + str(i)
            fn += "."
            fn += fn_ext 
                
            if i > 99999:
                print 'problem in uniqueFn, more than 100k files'
                return None
            elif fn in files:
                continue
            else:
                return fn
    
    if method == "guid":
        print 'not implemented yet'
        return "12345678." + fn_ext



def test_uniqueFn_1():
    ''' test increment method '''
    
    TEST_DIR = "data/test/uniquefn/test1/"
    NEW_FN = "testfn5.txt"

    files = os.listdir(TEST_DIR)

    if NEW_FN in files:
        os.remove(TEST_DIR + NEW_FN)

    files = os.listdir(TEST_DIR)
    assert NEW_FN not in files

    newFn = uniqueFn(fn_base = "testfn"
                    ,fn_dir = TEST_DIR
                    ,fn_ext = "txt"
                    )

    assert newFn == NEW_FN

def test_uniqueFn_2():
    ''' test increment method past first digit '''

    TEST_DIR = "data/test/uniquefn/test2/"
    NEW_FN = "testfn11.txt"

    for i in range(1,11):
        f = open(TEST_DIR + "testfn" + str(i) + ".txt", "w")
        f.close()
    
    files = os.listdir(TEST_DIR)
    assert len(files) == 10
    assert NEW_FN not in files

    newFn = uniqueFn(fn_base = "testfn"
                    ,fn_dir = TEST_DIR
                    ,fn_ext = "txt"
                    )

    assert newFn == NEW_FN

    for _f in os.listdir(TEST_DIR):
        os.remove(TEST_DIR + _f)

    assert len(os.listdir(TEST_DIR)) == 0
    

def test_uniqueFn_3():
    ''' test increment method with different ext '''
 
    TEST_DIR = "data/test/uniquefn/test3/"
    NEW_FN = "testfn1.h264"

    assert NEW_FN not in os.listdir(TEST_DIR)

    newFn = uniqueFn(fn_base = "testfn"
                    ,fn_dir = TEST_DIR
                    ,fn_ext = "h264"
                    )

    assert newFn == NEW_FN


def test_uniqueFn_4():
    ''' test increment method with different base_fn '''
 
    TEST_DIR = "data/test/uniquefn/test4/"
    NEW_FN = "justfn1.txt"

    assert len(os.listdir(TEST_DIR)) > 0
    assert NEW_FN not in os.listdir(TEST_DIR)

    newFn = uniqueFn(fn_base = "justfn"
                    ,fn_dir = TEST_DIR
                    ,fn_ext = "txt"
                    )

    assert newFn == NEW_FN

def test_uniqueFn_5():
    ''' test increment method with ext=None '''

    
