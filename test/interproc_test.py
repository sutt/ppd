import os, sys, copy, time, pickle
import cv2
import numpy as np
sys.path.append('../')
from modules.Interproc import GuiviewState, DBInterface

def test_load_gs_1():
    
    path_test = '''data/test/evalhelpers/EvalDataset_2/'''
    path_gs = os.path.join('..', path_test, 'input_gs.db')

    db = DBInterface(path_gs)
    listGS = [pickle.loads(d[1]) for d in db.selectAll()]

    #validate frameCounter
    ANSWER = [0,1,5]
    assert [gs.frameCounter for gs in listGS] == ANSWER

    #validate frame/origFrame exists
    assert listGS[0].getOrigFrame().shape == (480, 640, 3)
    assert listGS[1].getOrigFrame().shape == (480, 640, 3)

    #validate displayInputScore exists in some/ not in others
    ANSWER = {u'0': {u'data': [107, 214, 54, 52], u'type': u'circle'},u'1': {u'data': [111, 218, 46, 44], u'type': u'circle'}}
    assert cmp(listGS[0].displayInputScore, ANSWER) == 0    
    assert listGS[1].displayInputScore is None
