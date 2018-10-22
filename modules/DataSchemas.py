import copy

'''
    [ ] How to modify an existing score
    [ ] Object Types: an enum
        BALL_A - a stationary ball
        BALL_B - a ball in motion
        BALL_C - something in between?
    [ ] Object Enums, e.g. 1=ball, 2= ball reflection, 3=drone, 4=drone reflection
    [ ] Circle vs Ray Score types
    [ ] score_types as training vs challenge

    [ ] Add score types to data
    [ ] Add score type to gui
    [ ] add a .reset() method
    
    Notes:
        tagging #TODO-SS for relvant areas 

    Display: .scoreRect .roiRectScoring | .circleTrack
    NotesFactory:  .frameScoring  

'''


class ScoreSchema:

    '''
        Here we store (multiple) entrie(s) and query it when needed.
    '''
    
    def __init__(self):
        self.data = {}
        self.bLoaded = False

    def load(self, objScoring):
        ''' load a dict object as data '''
        try:
            assert objScoring is not None
            assert isinstance(objScoring, dict)
            self.data = copy.deepcopy(objScoring)
            self.bLoaded = True
        except:
            self.data = {}
            self.bLoaded = False

    def loadLegacy(self, listScoring):
        ''' load legacy score which is stored as list of 4 int's '''
        try:
            assert len(listScoring) == 4
            assert all( [isinstance(x, int) for x in listScoring])
            self.data['1'] = copy.copy(listScoring)
            self.bLoaded = True
        except:
            self.data = {}
            self.bLoaded = False


    def add(self, newScore):
        #add attributes this record
        self.data['1'] = newScore

    def addCircle(self, newCircle):
        ''' add a simple circle score'''
        self.data['1'] = newCircle

    def addRay(self, newRayTuple):
        pass

    def get(self, **kwargs):
        #select data record with certain attributes
        return self.data['1']

    def getDefault(self):
        if not(self.bLoaded):
            return None
        return self.data.get('1', None)


