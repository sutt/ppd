import os, sys, copy, time
import numpy as np
import pickle
import sqlite3
from modules.DataSchemas import ScoreSchema


'''
    build a prototype for interproc communication

    Ideas:

        Ultimately, need a list of these frames

    Dataset:

        lag intervals
        
        tracker-state

    Need Common operations methods on 

        GuiviewState.get_zoom_window()

        and operations like show multiple frames in 1-img

    TODOs

        [x] db interface class
            [x] open a connection
        [X] add to gui
        [x] add functionality to guiview
        [x] test w/ ipy
        [ ] add pathToData() function (see chess workspace)
        [x] add id as primary_key increment function (?)
        [ ] test that ScoreSchemas load from pickle?
        [ ] add datetime to state_tbl
            [ ] then helper function like get all from 'last 30 seconds'



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

    def getOrigFrame(self):
        ''' returns origFrame as numpy obj, instead of a 
            serialized string '''
        return np.loads(self.serial_origFrame)

    
    def getZoomWindow(self):
        ''' returns a zoom window from origFrame + zoomRect'''
        
        if (self.zoomRect is None) or (self.serial_origFrame is None):
            return None

        frame = self.getOrigFrame()



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

    


DATA_DIR = "../data/usr/demo.db"

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



