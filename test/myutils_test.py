import os, sys, copy
sys.path.append("../")
from modules.myutils import (uniqueFn, parseCommas, parseCliList)


def test_uniqueFn_1():
    ''' test increment method '''
    
    TEST_DIR = "../data/test/uniquefn/test1/"
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

    TEST_DIR = "../data/test/uniquefn/test2/"
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
 
    TEST_DIR = "../data/test/uniquefn/test3/"
    NEW_FN = "testfn1.h264"

    assert NEW_FN not in os.listdir(TEST_DIR)

    newFn = uniqueFn(fn_base = "testfn"
                    ,fn_dir = TEST_DIR
                    ,fn_ext = "h264"
                    )

    assert newFn == NEW_FN


def test_uniqueFn_4():
    ''' test increment method with different base_fn '''
 
    TEST_DIR = "../data/test/uniquefn/test4/"
    NEW_FN = "justfn1.txt"

    assert len(os.listdir(TEST_DIR)) > 0
    assert NEW_FN not in os.listdir(TEST_DIR)

    newFn = uniqueFn(fn_base = "justfn"
                    ,fn_dir = TEST_DIR
                    ,fn_ext = "txt"
                    )

    assert newFn == NEW_FN

def test_uniqueFn_5():
    ''' test increment method with ext=None 
        file contents: a1.txt, a2.txt, a1.bmp, a2.bmp, a3.bmp
    '''
    TEST_DIR = "../data/test/uniquefn/test5/"

    newFn = uniqueFn(fn_base="a", fn_dir = TEST_DIR, fn_ext=None)

    assert newFn == "a4"

def test_uniqueFn_6():
    ''' test increment method with ext=None and multi-dot file names
        file contents: a1.txt, a2.txt, a.diff.1.bmp, a.a2.bmp, a3.bmp
    '''
    TEST_DIR = "../data/test/uniquefn/test6/"

    newFn = uniqueFn(fn_base="a", fn_dir = TEST_DIR, fn_ext=None)

    assert newFn == "a4"


def test_uniqueFn_7():
    ''' test guid method '''
    import copy

    results = []
    
    N = 20
    for trial in range(N):

        results.append(
            uniqueFn("", method="guid", fn_ext="txt")
        )
    
    assert len(results) == N

    assert all(map(lambda fn: len(fn) == 6+1+3, results))

    for i in range(len(results)):
        
        _results2 = copy.copy(results)
        _results2.pop(i)
        elem = results[i]

        assert len(_results2) == N - 1
        
        assert elem not in _results2

def test_parseCommas_1():
    
    arg_1 = "1,2,3"
    arg_3 = "(1,2,3)"
    
    assert parseCommas(arg_1, bInt=True) == (1,2,3)
    assert parseCommas(arg_3, bInt=True) == (1,2,3)