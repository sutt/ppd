import os, sys, copy, time
import numpy as np
import cv2
import pickle
import sqlite3
from DataSchemas import ScoreSchema
from imgutils import crop_img
from ControlDisplay import Display


'''

    defines GuiveiwState and DBInterface which together let us 
    move *state* from guiview into jupyter: interproc-communication.
    
'''

class GuiviewState:

    def __init__(self):
        
        self.serial_origFrame = None
        self.displayInputScore = None
        self.displayOutputScore = None
        self.zoomRect = None
        self.scoreRect = None

        self.frameCounter = None
        
        self.trackParams = None

        self.currentCumTime = None

        self.orientation = None
        self.currentFrameNote = None
        self.vidBaseNote = None
        
        
    def setState( self
                 ,display
                 ,frameFactory
                 ,trackFactory
                 ,timeFactory
                 ,notesFactory
                 ):

        
        #display
        self.serial_origFrame = display.getOrigFrame().dumps()
        self.displayInputScore = display.inputScore.getAll()
        self.displayOutputScore = display.outputScore.getAll()
        self.zoomRect = copy.copy(display.zoomRect)
        self.scoreRect = copy.copy(display.scoreRect)
        
        #frame
        self.frameCounter = frameFactory.getFrameCounter()

        #track
        self.trackParams = trackFactory.getTrackParams()

        #time
        self.currentCumTime = timeFactory.cumTimeCurrent()

        #notes
        self.currentFrameNote = notesFactory.getFrameNoteCurrent()
        self.vidBaseNote = notesFactory.getBaseMetaLog()
        self.orientation = notesFactory.getOrientation()

    
    def save(self):
        
        return pickle.dumps(self)


    # helpers ---------

    def getOrigFrame(self, b_cvt_color = False):
        ''' returns origFrame as numpy obj, instead of a 
            serialized string '''
        img = np.loads(self.serial_origFrame)
        if b_cvt_color:
            return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return img

    @staticmethod
    def cvtColor(img):
        ''' convert cv2 BGR array to matplotlib RGB array '''
        try:
            _shape = img.shape
            if len(_shape) == 3:
                if _shape[2] == 3:
                    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        except:
            pass
        
        return img

        


    
    def initDisplay(self, zoomFct=None):
        ''' this is confusing and should be called automatically on init'''

        self.display = Display()
        self.display.setInit(showOn=False
                            ,scoreOff=False
                            ,frameResize=True
                            ,frameAnnotateFn=False
                            ,zoomFct=zoomFct)
        self.display.setFrame(self.getOrigFrame())
        
        #added for more capabilities
        self.display.scoreOn = True
        self.display.bShowScoring = True
        self.display.scoreRect = self.scoreRect
        self.display.inputScore.load(copy.deepcopy(self.displayInputScore))
        self.display.frameAnnotateFn = False
        self.display.zoomAnnotateSize = False
        self.display.alterFrame()
    
    def getZoomWindow(self, inputRect=None):
        ''' returns a zoom window from origFrame + zoomRect'''

        frame = self.getOrigFrame()

        if inputRect is None:
            # only scale for zoomRect, other rects are in terms or orig
            _rect = self.zoomRect
            crop_rect = [self.display.scaleMainToOrig(p) for p in _rect]
        else:
            crop_rect = inputRect
        
        crop_rect = tuple(crop_rect)
        
        zoom_img = crop_img( frame
                            ,self.display.absRect(crop_rect)
                            )
        return zoom_img

    
    def drawTracker(self, trackRect):
        ''' draw track onto self.display.frame using trackRect'''

        self.display.zoomOn = False
        self.display.trackOn = True
        self.display.trackScore.addCircle(trackRect, 0)
        
        self.display.drawTrackers()
        

    def drawOperator(self, scoreRect):
        ''' draw score onto self.display.frame using trackRect'''

        self.display.zoomOn = False
        self.display.scoreOn = True
        self.display.bShowScoring = True
        self.display.inputScore.addCircle(scoreRect, 0)
        
        self.display.drawOperators()

    def getScoreWindow(self, bScoreFrame = True):
        ''' return window in self.display.scoreRect; use
            drawTracker(), drawOperator() before this get annotations
            bScoreFrame = True: use the scoreFrame in this class
                (which is created in self.initDisplay() + display.alterFrame())
            bScoreFrame = False: clip from display.frame
        '''

        if bScoreFrame:
            
            score_img = self.display.scoreFrame.copy()

        else:

            score_img = crop_img( self.display.frame.copy()
                                    ,self.display.absRect(
                                        tuple(self.display.scoreRect)
                                    )
                                )
        return score_img



class GuiviewStateHelper(GuiviewState):

    '''     NOT IMPLEMENTED 
    
        Inherits GuiviewState, which should be data-populated.
        Adds multiple helpers methods to use this data in Jupyter.
    '''
    
    def __new__(cls, inputGuiviewState):
        inputGuiviewState.__class__ = GuiviewStateHelper
        print '__new'
        return inputGuiviewState
    
    def __init__(self, inputGuiviewState):
        # GuiviewState.__init__(self)
        # inputGuiviewState.__init__()
        print '__init'
        pass

    
    def getOrigFrame(self):
        ''' returns origFrame as numpy obj, instead of a 
            serialized string '''
        return np.loads(self.serial_origFrame)

    
    def getZoomWindow(self):
        ''' returns a zoom window from origFrame + zoomRect'''
        
        if (self.zoomRect is None) or (self.serial_origFrame is None):
            return None

        frame = self.getOrigFrame()

    


DATA_DIR = "../data/usr/interproc.db"

class DBInterface:

    def __init__(self, data_dir = DATA_DIR):
        
        self.conn = sqlite3.connect(data_dir)
        self.c = self.conn.cursor()

        if not(self.verifyTable()):
            self.createTable()

    def verifyTable(self):
        try:    
            self.c.execute("SELECT * FROM state_tbl")
            return True
        except:
            pass
        return False

    def createTable(self):
        s = """CREATE TABLE state_tbl (id integer primary key, state text)"""
        self.c.execute(s)
        self.conn.commit()

    def deleteTable(self):
        s = "drop table state_tbl"
        self.c.execute(s)
        self.conn.commit()

    def insertState(self, state):
        s = """INSERT INTO state_tbl(state) VALUES(?)"""
        self.c.execute(s, (state,))
        self.conn.commit()

    def insertStateGetId(self, state):
        ids_0 = self.getIds() 
        self.insertState(state)
        ids_1 = self.getIds()
        return filter(lambda _id: _id not in ids_0, ids_1)[0]

    def getIds(self):
        self.c.execute('select id from state_tbl')
        rows = self.c.fetchall()
        return [elem[0] for elem in rows]

    def deleteAll(self):
        self.c.execute('delete from state_tbl')
        self.conn.commit()

    def selectAll(self):
        self.c.execute("select * from state_tbl")
        rows = self.c.fetchall()
        return rows

    def selectLatest(self):
        s = """select * from state_tbl 
                where id = (select max(id) from state_tbl) """
        self.c.execute(s)
        row = self.c.fetchall()
        try:
            assert len(row) == 1
        except:
            print 'there is more than 1 record in this result!'
        return row


    def viewAll(self):
        self.c.execute("select id from state_tbl")
        rows = self.c.fetchall()
        return rows

