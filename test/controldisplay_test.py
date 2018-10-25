import os, sys, copy, json
import subprocess
import time

sys.path.append("../")
from modules.ControlDisplay import Display

def test_mindimsforrect_1():
    ''' simple min_scalar_wdith examples '''

    BOUNDS = (480, 640)

    rect = (100, 100, 100, 10)
    out = Display.minDimsForRect(
                        rect
                        ,BOUNDS
                        ,min_scalar_width=20
                        ,max_multiple_width=None
                        )
    assert out == (100,95,100,20)

    rect = (100, 100, 10, 100)
    out = Display.minDimsForRect(
                        rect
                        ,BOUNDS
                        ,min_scalar_width=20
                        ,max_multiple_width=None
                        )
    assert out == (95,100,20,100)

    rect = (100, 100, 10, 10)
    out = Display.minDimsForRect(
                        rect
                        ,BOUNDS
                        ,min_scalar_width=20
                        ,max_multiple_width=None
                        )
    assert out == (95,95,20,20)


def test_mindimsforrect_2():
    ''' min_scalar_wdith with non modulo-zero expansion '''

    BOUNDS = (480, 640)

    rect = (100, 100, 100, 5)
    out = Display.minDimsForRect(
                        rect
                        ,BOUNDS
                        ,min_scalar_width=10
                        ,max_multiple_width=None
                        )
    assert out == (100,97,100,10)


def test_mindimsforrect_3():
    ''' min_scalar_wdith examples: that collide with bounds '''
    
    BOUNDS = (480, 640)

    rect = (0, 0, 100, 10)
    out = Display.minDimsForRect(
                        rect
                        ,BOUNDS
                        ,min_scalar_width=20
                        ,max_multiple_width=None
                        )
    assert out == (0, 0, 100, 20)

    rect = (630, 100, 10, 100)
    out = Display.minDimsForRect(
                        rect
                        ,BOUNDS
                        ,min_scalar_width=20
                        ,max_multiple_width=None
                        )
    assert out == (620, 100, 20, 100)

    rect = (630, 100, 10, 100)
    out = Display.minDimsForRect(
                        rect
                        ,BOUNDS
                        ,min_scalar_width=20
                        ,max_multiple_width=None
                        )
    assert out == (620, 100, 20, 100)


def test_mindimsforrect_4():
    ''' check that max_multiple_wdith does not interfere with
         min_scalar_width 
    '''

    BOUNDS = (480, 640)

    rect = (100, 100, 100, 10)
    out = Display.minDimsForRect(
                        rect
                        ,BOUNDS
                        ,min_scalar_width=20
                        ,max_multiple_width=20
                        )
    assert out == (100,95,100,20)

    rect = (100, 100, 10, 100)
    out = Display.minDimsForRect(
                        rect
                        ,BOUNDS
                        ,min_scalar_width=20
                        ,max_multiple_width=20
                        )
    assert out == (95,100,20,100)


def test_mindimsforrect_5():
    ''' simple max_multiple_wdith '''

    BOUNDS = (480, 640)

    rect = (100, 100, 100, 10)
    out = Display.minDimsForRect(
                        rect
                        ,BOUNDS
                        ,min_scalar_width=None
                        ,max_multiple_width=5
                        )
    assert out == (100,95,100,20)

    rect = (100, 100, 10, 100)
    out = Display.minDimsForRect(
                        rect
                        ,BOUNDS
                        ,min_scalar_width=None
                        ,max_multiple_width=5
                        )
    assert out == (95,100,20,100)

def test_mindimsforrect_6():
    ''' max_multiple_width examples: that collide with bounds '''
    
    BOUNDS = (480, 640)

    rect = (0, 0, 100, 10)
    out = Display.minDimsForRect(
                        rect
                        ,BOUNDS
                        ,min_scalar_width=None
                        ,max_multiple_width=5
                        )
    assert out == (0, 0, 100, 20)

    rect = (630, 100, 10, 100)
    out = Display.minDimsForRect(
                        rect
                        ,BOUNDS
                        ,min_scalar_width=None
                        ,max_multiple_width=5
                        )
    assert out == (620, 100, 20, 100)


def test_display_rectToCircle():
    
    rect = (0,0,10,10)
    x,y,r = Display.rectToCircle(rect)

    assert x == 5
    assert y == 5 
    assert r == 5

    rect = (2,1,10,12)
    x,y,r = Display.rectToCircle(rect)

    assert x == 7
    assert y == 7 
    assert r == 5

    rect = (2,1,11,12)
    x,y,r = Display.rectToCircle(rect)

    assert x == 7
    assert y == 7 
    assert r == 5

if __name__ == "__main__":
    test_mindimsforrect_1()