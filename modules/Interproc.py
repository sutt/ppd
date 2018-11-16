import os, sys
import numpy as np
import pickle
import sqlite3
from modules.DataSchemas import ScoreSchema


'''
    build a prototype for interproc communication

    Ideas:

        can just reload functionality in ipython

        can go over a database

        we'll need to pack media like images

        ultimately, we'll need lists of these @frame instance

    Dataset:

        orig-img
        zoom-window
        score-window
        timelog cumtime, lag intervals
        noteslog - score
        display.current_score
        
        display parameters, e.g. zoom window

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
        [ ] add id as primary_key increment function (?)



'''

class GuiviewState:

    def __init__(self):
        
        self.serial_origFrame = None
        self.frameCounter = None
        self.displayOutputScore = None
        self.displayInputScore = None
        self.trackParams = None
        
        self.dummy = None
        self.img = None


    def saveState(self, display, frameFactory, trackFactory):

        self.serial_origFrame = display.getOrigFrame().dumps()

        self.frameCounter = frameFactory.getFrameCounter()
        print self.frameCounter

        self.displayInputScore = display.inputScore.getAll()

        self.displayOutputScore = display.outputScore.getAll()

        self.trackParams = trackFactory.getTrackParams()

    
    def save(self):
        
        return pickle.dumps(self)

    
    def getOrigFrame(self):
        return np.loads(self.serial_origFrame)



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
        s = """CREATE TABLE state_tbl (id text, state text)"""
        self.c.execute(s)
        self.conn.commit()

    def insertState(self, state):
        s = """INSERT INTO state_tbl(id, state) VALUES(?,?)"""
        self.c.execute(s, ('1', state))
        self.conn.commit()

    def deleteAll(self):
        self.c.execute('delete from state_tbl')
        self.conn.commit()

    def selectAll(self):
        self.c.execute("select * from state_tbl")
        rows = self.c.fetchall()
        return rows



# test ipy reload --------------
def hello():
    return 2

class MyClass:

    def __init__(self):
        pass

    def myMethod(self):
        return 2

# build flask app -------------------

# app = Flask(__name__)