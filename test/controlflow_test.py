import os, sys, copy, json
import subprocess
import time

sys.path.append("../")
from modules.ControlFlow import FrameFactory
from modules.ControlFlow import TimeFactory
from modules.ControlFlow import DirectoryFactory
from modules.ControlFlow import NotesFactory
import modules.GlobalsC as g



def test_recursekeys_1():
    
    nf = NotesFactory
    
    a = {"a":1, "b":2}
    a_keys, a_vals = nf.recurseKeys(a)
    assert a_keys == ["a", "b"]

    b = {"a":1, "b":2, "c": {"c_a":17}}
    b_keys, b_vals = nf.recurseKeys(b)
    check = [ (elem in ["a", "b", ["c", "c_a"]  ] ) for elem in b_keys]
    assert all(check)

    b = {"a":1, "b":2, "c": {"c_a":17}}
    b_outer = {"x":"1"}
    b_outer['outer'] = b
    b_keys, b_vals = nf.recurseKeys(b_outer)
    
    assert "x" in b_keys
    assert  all([
        (elem in ["outer", "a", "b", ["c", "c_a"]  ] ) 
        for elem in b_keys[1]
        ])


def test_mergedict_1():
    ''' test basic functionality for mergedict '''

    #simple ----
    main, update = {}, {}

    main['key1'] = "a"
    main["key2"] = {"subA": 1, "subB": "two"}
    
    update["key1"] = "newData"
    
    out = NotesFactory.mergeDicts(main, update)
    
    assert out['key1'] == "newData"
    
    
    #more complex ---
    main, update = {}, {}
    
    main['key1'] = "a"
    main["key2"] = {"subA": 1, "subB": "two"}

    update = {"key2":{"subB": 99}}

    out = NotesFactory.mergeDicts(main, update)

    assert out['key2']["subB"] == 99
    assert out['key1'] == "a"
    assert out['key2']['subA'] == 1


def test_mergedict_2():
    ''' test bad inputs '''

    #1-bad-update ----
    main, update = {}, {}

    main = {"key1": "a", "key2":{"subA": 1, "subB": "two"}}
    
    update = {"not a key": 99}
    
    out = NotesFactory.mergeDicts(main, update)
    
    assert out == main
    
    
    #1-bad, 1-good for update ---
    main, update = {}, {}

    main = {"key1": "a", "key2":{"subA": 1, "subB": "two"}}
    
    update = {"not a key": 99, "key2":{"subB": 99}}
    
    out = NotesFactory.mergeDicts(main, update)
    
    assert out["key2"]["subB"] == 99
    assert not("not a key" in out.keys())

def test_mergedict_3():
    ''' test how this works for ScoreSchema situtations '''

    # simple add record
    main = {
                "0":{
                    "type":"circle",
                    "data": [202, 162, 48, 43]
                },
                "1":{
                    "type":"circle",
                    "data": [100, 162, 48, 43]
                }
			}

    update = {
                "7":{
                    "type":"circle",
                    "data": [202, 162, 48, 43]
                }
			}

    
    out = NotesFactory.mergeDicts(main, update, b_add=True)
    print out

    assert all( [k in ("0", "1", "7") for k in out.keys()] )
    assert out["7"]["data"] == [202, 162, 48, 43]

    # overwrite record
    main = {
                "0":{
                    "type":"circle",
                    "data": [202, 162, 48, 43]
                },
                "1":{
                    "type":"circle",
                    "data": [100, 162, 48, 43]
                }
			}

    update = {
                "1":{
                    "type":"ray",
                    "data": [0,0,0,0]
                }
			}

    out = NotesFactory.mergeDicts(main, update, b_add=True)

    assert len(out.keys()) == 2
    assert out["1"]["type"] == "ray"
    assert out["1"]["data"] == [0,0,0,0]

    # overwrite + add
    main = {
                "0":{
                    "type":"circle",
                    "data": [202, 162, 48, 43]
                },
                "1":{
                    "type":"circle",
                    "data": [100, 162, 48, 43]
                }
			}

    update = {
                "1":{
                    "type":"ray",
                    "data": [0,0,0,0]
                },
                "7":{
                    "type":"ray",
                    "data": [1,1,1,1]
                },
			}

    out = NotesFactory.mergeDicts(main, update, b_add=True)

    
    assert len(out.keys()) == 3
    assert out["1"]["data"] == [0,0,0,0]
    assert out["7"]["data"] == [1,1,1,1]



if __name__ == "__main__":
    test_mergedict_3()