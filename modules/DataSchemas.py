import copy

'''
   
   defines ScoreSchema for handling tracking multiple objects

'''


class ScoreSchema:

    '''
        Here we store values for a frameNote or for Display-class scoring:

        data: {
        
                objEnum (str): {

                    type: (str)  "circle" or "ray"
                    data: (list of int)
                }
        }

            objEnum - 0 to 3, corresponds to distinct object being tracked
            type - scoring type, a circle or a ray
            data - data which represents the scores position:
                for circle: a rect
                for ray, a 2-ple of (x,y)'s
    '''
    
    def __init__(self):
        self.data = {}
        self.bLoaded = False
        self.bHasContents = False

    def reset(self):
        self.data = {}
        self.bLoaded = False
        self.bHasContents = False

    def checkHasContents(self):
        ''' return True if data has been poppulated;
            a fast method for boolean type check '''
        return self.bHasContents

    def checkHasValid(self):
        ''' return True if any shape has a reasonable trackRoi '''
        try:
            for k in self.data.keys():
                _type = self.data[k]['type']
                _data = self.data[k]['data']
                if _type != 'circle': 
                    continue
                if all([x >= 0 for x in _data]):
                    return True
            return False
        except:
            return False
        
    @staticmethod
    def _coerceDataToInt(objData):
        ''' handles objData as list/tuple or list/tuple-of-list/tuple '''
        
        if ((type(objData[0]) is list) or (type(objData[0]) is tuple)):
            return map(lambda tup: map(int, tup), objData)    
        else:
            return map(int, objData)

    
    def load(self, objScoring):
        ''' load a dict object as data '''
        try:
            assert objScoring is not None
            assert isinstance(objScoring, dict)
            
            for _objEnum in objScoring.keys():
                assert isinstance(objScoring[_objEnum]['data'], list)
                objScoring[_objEnum]['data'] = self._coerceDataToInt(objScoring[_objEnum]['data'])
            
            self.data = copy.deepcopy(objScoring)
            self.bLoaded = True
            self.bHasContents = True
        except:
            try:
                self.loadLegacy(objScoring)
            except:
                self.data = {}
                self.bLoaded = False
                self.bHasContents = False

    def loadLegacy(self, listScoring):
        ''' load legacy score which is type=circle and 
            stored as list of 4 int's '''
        try:
            assert len(listScoring) == 4
            assert all( [isinstance(x, int) for x in listScoring])
            self.addCircle(copy.copy(listScoring))
            self.bLoaded = True
            self.bHasContents = True
        except:
            self.data = {}
            self.bLoaded = False
            self.bHasContents = False


    def add(self, scoreData, scoreType=None, objEnum=0):
        ''' a generalized way to add to data '''
        
        if scoreData is None:
            return
        
        if scoreType is None:
            self.addCircle(scoreData, objEnum=objEnum)
        elif scoreType == 'circle':
            self.addCircle(scoreData, objEnum=objEnum)
        elif scoreType == 'ray':
            self.addRay(scoreData, objEnum=objEnum)
        else:
            print 'failed to find scoreType add() to scoreSchema'
        

    def addCircle(self, circleData, objEnum=0):
        ''' add a circle score. data format: (x,y,w,h) '''
        _score = {}
        _score['type'] = 'circle'
        _score['data'] = map(int, circleData)
        self.data[str(objEnum)] = _score
        self.bHasContents = True


    def addRay(self, rayData, objEnum=0):
        ''' add a ray score. data format: ((x0,y0), (x1,y1))'''
        _score = {}
        _score['type'] = 'ray'
        _score['data'] = map(lambda tup: map(int, tup), rayData)
        self.data[str(objEnum)] = _score
        self.bHasContents = True


    def addRayPoint(self, rayPoint, rayPointEnum, objEnum=0):
        ''' for adding a ray object, but with only 1 point 
            available at the time. note: we want a convention
            on whether point 0 is start or end of bounce '''

        b_exists = False
        if self.data.get(str(objEnum), None) is not None:
            b_exists = True

        b_overwrite = False
        try:
            if self.data.get(str(objEnum), {}).get('type') != 'ray':
                b_overwrite = True
        except:
            pass
        
        if b_exists and not(b_overwrite):
            
            _score = self.data[str(objEnum)]
            _rayData = _score['data']
            _rayData[rayPointEnum] = rayPoint
            _score['data'] = _rayData
            
            if all([x is not None for x in _rayData]):
                self.bHasContents = True
        else:
            
            _score = {}
            _score['type'] = 'ray'
            _rayData = [None, None]
            _rayData[rayPointEnum] = rayPoint
            _score['data'] = _rayData

        self.data[str(objEnum)] = _score


    @staticmethod
    def _validateScoreEntry(scoreEntry):
        ''' return True if valid scoreEntry '''
        pass

    def getObjRect(self, objEnum):
        ''' return relative rect bounding score-obj'''

        _data = self.data.get(str(objEnum), {}).get('data', None)
        _type = self.data.get(str(objEnum), {}).get('type', None)
        
        if _data is None or _type is None: 
            return None

        if _type == 'circle':
            return tuple(_data)

        minX = min(_data, key=lambda elem: elem[0])[0]
        maxX = max(_data, key=lambda elem: elem[0])[0]
        minY = min(_data, key=lambda elem: elem[1])[1]
        maxY = max(_data, key=lambda elem: elem[1])[1]

        x, y = minX, minY
        dx = max(maxX - minX, 1)
        dy = max(maxY - minY, 1)

        return (x, y, dx, dy)

    
    def getNumObjs(self):
        try: return len(self.data.keys())
        except: return 0

    def get(self, objEnum=0):
        return self.data.get(str(objEnum), None)

    def getData(self, objEnum=0):
        return self.data.get(str(objEnum),{}).get('data', None)

    def getAll(self):
        if self.data == {}:
            return None
        return copy.deepcopy(self.data)

    def getListType(self, _type):
        ''' return list of (enum, data) for each obj of type _type'''
        listObjs = []
        for k in self.data.keys():
            if self.data[k].get('type') == _type:
                listObjs.append((k, self.data.get(k).get('data')))
        return listObjs
    
    def getDefault(self):
        ''' legacy method, should not be used except for convenience'''

        if self.bLoaded:
            
            try:
                keys = self.data.keys()
                keys.sort()
                firstKey = keys[0]

            except:
                fristKey = '0'
            
            scoreDict = self.data.get(firstKey, None)
            
            if scoreDict is not None:

                return scoreDict.get('data', None)

        return None

    @staticmethod
    def getScalarFields(num_objs=4, num_data_cols=4):
        ''' return list of str, representing col names for this score_schema

            num_objs (int) total number of objects to repeat this for
            num_data_cols (int)

                obj_exists_<objI>, 
                obj_type_<objI>, 
                data<0>_<objI>, data<1>_<objI>, ...data<num_data_cols>_<objI>
        '''
        fields = []

        scalar_fields = ['obj_exists','obj_type']
        data_fields = ['data' + str(i) for i in range(num_data_cols)]
        scalar_fields.extend(data_fields)
        
        for _objI in range(num_objs):
            
            _fields = copy.copy(scalar_fields)
            _fields = [str(elem) + '_' + str(_objI) for elem in _fields]
            fields.extend(_fields)

        return copy.copy(fields)


    def toScalars(self, num_data_cols=4):
        '''
            return dict with keys and values corresponding to all objEnums
            that exists. keys:  (I=objEnum)
                obj_exists_I
                obj_type_I
                data0_I
                ...
                data<num_cols>_I
        '''

        if not(self.checkHasContents):
            return None

        outputDict = {}
        for _objEnum in self.data.keys():
            
            outputDict['obj_exists_' + str(_objEnum)] = True

            outputDict['obj_type_' + str(_objEnum)] = self.data[_objEnum].get('type', None)

            _dataStruct = self.data[_objEnum].get('data', None)

            if _dataStruct is None:
                continue
            
            for iCol in range(num_data_cols):
                
                _val = None
                
                if self.data[_objEnum].get('type', None) == 'circle':
                    
                    if iCol < len(_dataStruct):
                        _val = _dataStruct[iCol]

                elif self.data[_objEnum].get('type', None) == 'ray':

                    if iCol < 4:
                        _val = _dataStruct[iCol / 2][iCol % 2]

                else:
                    
                    #TODO - add warning
                    if iCol < len(_dataStruct):
                        _val = _dataStruct[iCol]

                outputDict['data' + str(iCol) + '_' + str(_objEnum)] = _val
        
        return outputDict

    def fromScalarsAddObject(self,objEnum=0,**kwargs):
        ''' pass in a dict for arguments:
            make sure to change objEnum or you'll overwrite existing data
        '''
        _type = kwargs.get('objtype', 'circle')

        _data0 = kwargs.get('data0', None)
        _data1 = kwargs.get('data1', None)
        _data2 = kwargs.get('data2', None)
        _data3 = kwargs.get('data3', None)

        if _type == 'circle':

            self.addCircle([_data0, _data1, _data2, _data3], objEnum=objEnum)

        elif _type == 'ray':

            self.addRay([[_data0, _data1], [_data2, _data3]], objEnum=objEnum)

        




