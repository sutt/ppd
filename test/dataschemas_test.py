import os, sys
sys.path.append("../")
from modules.DataSchemas import ScoreSchema



def test_getScalarFields():

    fields = ScoreSchema.getScalarFields()
    ANSWER = ['obj_exists_0', 'obj_type_0', 'data0_0', 'data1_0', 'data2_0', 'data3_0', 'obj_exists_1', 'obj_type_1', 'data0_1', 'data1_1', 'data2_1', 'data3_1', 'obj_exists_2', 'obj_type_2', 'data0_2', 'data1_2', 'data2_2', 'data3_2', 'obj_exists_3', 'obj_type_3', 'data0_3', 'data1_3', 'data2_3', 'data3_3']
    assert all( elem in ANSWER for elem in fields)
    assert all( elem in fields for elem in ANSWER)

    fields = ScoreSchema.getScalarFields(num_objs=1)
    ANSWER = ['obj_exists_0', 'obj_type_0', 'data0_0', 'data1_0', 'data2_0', 'data3_0']
    assert all( elem in ANSWER for elem in fields)
    assert all( elem in fields for elem in ANSWER)

    fields = ScoreSchema.getScalarFields(num_objs=1, num_data_cols=6)
    ANSWER = ['obj_exists_0', 'obj_type_0', 'data0_0', 'data1_0', 'data2_0', 'data3_0', 'data4_0', 'data5_0']
    assert all( elem in ANSWER for elem in fields)
    assert all( elem in fields for elem in ANSWER)


def test_toScalars():

    # test basic method
    score = {
                "0":{
                    "type":"circle",
                    "data": [100, 150, 60, 58]
                }
			}
    ss = ScoreSchema()
    ss.load(score)
    scalarsDict = ss.toScalars()

    ANSWER = {'obj_exists_0':True, 'obj_type_0': 'circle', 'data0_0':100, 'data1_0':150, 'data2_0':60, 'data3_0':58}
    assert cmp(scalarsDict, ANSWER) == 0

    # test method on ray-type object
    score = {
                "0":{
                    "type":"ray",
                    "data": [[100, 150], [60, 58]]
                }
			}
    ss = ScoreSchema()
    ss.load(score)
    scalarsDict = ss.toScalars()

    ANSWER = {'obj_exists_0':True, 'obj_type_0': 'ray', 'data0_0':100, 'data1_0':150, 'data2_0':60, 'data3_0':58}    
    assert cmp(scalarsDict, ANSWER) == 0
    
    # test multi-obj's + non-traditional objEnums
    score = {
                "1":{
                    "type":"circle",
                    "data": [100, 150, 60, 58]
                },
                "3":{
                    "type":"ray",
                    "data": [[100, 150], [60, 58]]
                }
			}
    ss = ScoreSchema()
    ss.load(score)
    scalarsDict = ss.toScalars()

    ANSWER = {'obj_exists_1':True, 'obj_type_1': 'circle', 'data0_1':100, 'data1_1':150, 'data2_1':60, 'data3_1':58, 'obj_exists_3':True, 'obj_type_3': 'ray', 'data0_3':100, 'data1_3':150, 'data2_3':60, 'data3_3':58}
    assert cmp(scalarsDict, ANSWER) == 0

    # test non-default num_data_cols argument
    score = {
                "0":{
                    "type":"circle",
                    "data": [100, 150, 60, 58]
                }
			}
    ss = ScoreSchema()
    ss.load(score)
    scalarsDict = ss.toScalars(num_data_cols=6)

    ANSWER = {'obj_exists_0':True, 'obj_type_0': 'circle', 'data0_0':100, 'data1_0':150, 'data2_0':60, 'data3_0':58, 'data4_0':None, 'data5_0':None}
    assert cmp(scalarsDict, ANSWER) == 0


def test_fromScalarsAddObject():

    ss = ScoreSchema()
    assert ss.getAll() is None

    fields = {'objtype':'circle', 'data0':100, 'data1':100, 'data2':40, 'data3':50, 'misc':'blah balh'}
    ss.fromScalarsAddObject(objEnum=0, **fields)
    assert ss.getAll() == {'0':{'type': 'circle', 'data': [100,100,40,50] }}

    # test overwrite of objEnum=0
    ss.fromScalarsAddObject(objEnum=0, **fields)
    assert ss.getAll() == {'0':{'type': 'circle', 'data': [100,100,40,50] }}

    # test multiple obj's
    fields2 = {'objtype':'circle', 'data0':200, 'data1':100, 'data2':30, 'data3':20, 'misc':'blah balh'}
    ss.fromScalarsAddObject(objEnum=3, **fields2)
    assert ss.getAll() == {'0':{'type': 'circle', 'data': [100,100,40,50] },
                           '3':{'type': 'circle', 'data': [200,100,30,20] }}


def test_ScoreSchema_addObj_number_type():

    # make sure all data gets converted to int-type
    
    # addCircle
    inp_data = [11.0, 12, float(15), float(0)]
    ss = ScoreSchema()
    ss.addCircle(inp_data, objEnum=0)
    ret_data = ss.getAll()['0']['data']
    assert all(map(lambda elem: type(elem) is int, ret_data))
    assert ret_data == [11,12,15,0]

    # addRay
    inp_data = [ [11.0, 12.9999], [float(15), float(0.1)]]
    ss = ScoreSchema()
    ss.addRay(inp_data, objEnum=0)
    ret_data = ss.getAll()['0']['data']
    assert all(map(lambda elem: type(elem) is int, ret_data[0]))
    assert all(map(lambda elem: type(elem) is int, ret_data[1]))
    assert ret_data == [[11,12],[15,0]]


def test_ScoreSchema_load_number_type():
    
    # test that we coerce all data into int

    # circle
    inp_data = {'0':{'type':'circle', 'data':[1.1,2,float(15), 0.9999]}}
    ss = ScoreSchema()
    ss.load(inp_data)
    ret_data = ss.getAll()['0']['data']
    assert  ret_data == [1,2,15,0]
    assert all(map(lambda elem: type(elem) is int, ret_data))

    # ray
    inp_data = {'0':{'type':'ray', 'data':[[1.1,2],[float(15), 0.9999]]}}
    ss = ScoreSchema()
    ss.load(inp_data)
    ret_data = ss.getAll()['0']['data']
    assert  ret_data == [[1,2],[15,0]]
    assert all(map(lambda elem: type(elem) is int, ret_data[0]))
    assert all(map(lambda elem: type(elem) is int, ret_data[1]))


def test_getObjRect_1():
    
    score = {
                "0":{
                    "type":"ray",
                    "data": [[100,50], [200, 75]]
                },
                "1":{
                    "type":"ray",
                    "data": [[200, 75], [100,50]]
                }
			}

    ss = ScoreSchema()
    ss.load(score)

    assert ss.getObjRect(0) == ss.getObjRect(1)

    assert ss.getObjRect(0) == (100, 50, 100, 25)

    score = {
                "0":{
                    "type":"ray",
                    "data": [[100,50], [200, 25]]
                }
			}

    ss.load(score)

    ss.getObjRect(0) == (100, 25, 100, 25)

def test_getObjRect_2():
    
    score = {
                "1":{
                    "type":"circle",
                    "data": [100,50, 99, 99]
                }
			}

    ss = ScoreSchema()
    ss.load(score)

    assert ss.getObjRect(1) == (100, 50, 99, 99)

def test_checkHasValid_1():

    score = {
                "0":{
                    "type":"circle",
                    "data": [20, 40, 50, 60]
                },
                "1":{
                    "type":"circle",
                    "data": [-10, -20, 40, 40]
                }
			}

    ss = ScoreSchema()
    ss.load(score)

    assert ss.checkHasValid()

    score = {
                "0":{
                    "type":"circle",
                    "data": [-10, 20, 40, 40]
                },
                "1":{
                    "type":"circle",
                    "data": [10, 20, -40, 40]
                }
			}

    ss = ScoreSchema()
    ss.load(score)

    assert ss.checkHasValid() == False

if __name__ == "__main__":
    test_ScoreSchema_load_number_type()