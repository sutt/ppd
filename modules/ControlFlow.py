import os, sys, time, copy, json, re
from collections import OrderedDict
import numpy as np
import cv2
import argparse
from vidwriter import VidWriter
from miscutils import uniqueFn
from modules.Utils import TimeLog
from modules.Utils import MetaDataLog
from modules.DataSchemas import ScoreSchema
from modules import GlobalsC as g

class FrameFactory:

    ''' Manage frames from an open VideoCapture(file) object or preloaded list:
        - manipulate/validate frameCounter
        - validate video begin/end; suggest break from this frameloop       
    '''

    def __init__(self):
        self.play = False
        self.advanceFrame = False
        self.retreatFrame = False
        self.writeAndAdvance = False
        self.rewindCmd = False
        self.fastforwardCmd = False
        self.preloaded = False
        self.semiloaded = False
        self.maxFramesSize = 10**9
        self.semiloadCounter = 0
        self.frames = []
        self.cam = None
        self.frameCounter = -1
        self.firstN = 0
        self.failedLoad = False


    def setCam(self, vidPathFn):
        self.cam = cv2.VideoCapture(vidPathFn)
        
        #TODO - raise opencv warning
        if not(self.cam.isOpened()):
            self.failedLoad = True

    def setFirstN(self, firstN):
        self.firstN = firstN

    def preload(self):
        
        try:
            while(self.cam.isOpened()):
                
                ret, frame = self.cam.read()

                if ret:
                    self.frames.append(frame)
                else:
                    break
                if sum([f.nbytes for f in self.frames]) > self.maxFramesSize:
                    print 'cant load full video; going semiloaded mode'
                    self.semiloaded = True
                    break

            if len(self.frames) > 0:
                self.preloaded = True

        except:
            return 


    def isOpened(self):
        
        if self.firstN > 0:
            if self.frameCounter > self.firstN:
                return False
        
        if self.semiloaded:
            return self.cam.isOpened()
        
        if self.preloaded:
        
            if self.frameCounter > len(self.frames) - 1:
        
                if self.playOn:
                    self.cam.release()
                    return False
                else:
                    return True
            else:
                return True
        else:
            return self.cam.isOpened()

    def getFrameSize(self):
        if self.preloaded:
            try:
                frameSize = (self.frames[0].shape[1], self.frames[0].shape[0])
                return frameSize
            except:
                return None
        else:
            raise Exception("Not implemented for not preload")

    def getFrame(self):
        if self.preloaded and not(self.semiloaded):
            
            if len(self.frames) - 1 < self.frameCounter:
                return False, None
            
            return True, self.frames[self.frameCounter]
            
        elif self.semiloaded:

            if self.semiloadCounter + len(self.frames) - 1 < self.frameCounter:
                
                ret, frame = self.cam.read()
                
                if ret:
                    self.frames.append(frame)
                    self.frames.pop(0)
                    self.semiloadCounter += 1
                    return True, frame
                else:
                    self.cam.release()
                    return False, None

            else:
                return True, self.frames[self.frameCounter - self.semiloadCounter]
        
        else:
            
            ret, frame = self.cam.read()
            if not(ret):
                self.cam.release()
                    
            return ret, frame

    def getFrameCounter(self):
        return self.frameCounter

    def getFrameTotal(self):
        if self.frames is None:
            return -1
        if self.semiloaded:
            return -1
        return len(self.frames) - 1

    def setPlay(self, playOn):
        self.playOn = playOn

    def setAdvanceFrame(self, advanceFrame):
        self.advanceFrame = advanceFrame
        g.switchAdvanceFrame = False

    def setRetreatFrame(self, retreatFrame):
        self.retreatFrame = retreatFrame
        g.switchRetreatFrame = False

    def setRewind(self, rewind):
        self.rewindCmd = rewind
        g.switchRewind = False

    def setFastforward(self, fastforward):
        self.fastforwardCmd = fastforward
        g.switchFastforward = False


    def deltaCounter(self, requestAmt, bypassValidation=False):
        
        if self.preloaded:
            
            if bypassValidation:
                self.frameCounter += requestAmt
                return True
            
            newCounter = requestAmt + self.frameCounter

            if self.semiloaded:
                
                if requestAmt == 1:
                    self.frameCounter += requestAmt
                    return True
                
                if requestAmt > 1:
                    return False
                    
                if requestAmt < 1:
                    
                    if newCounter < self.semiloadCounter:
                        return False
                    else:
                        self.frameCounter += requestAmt
                        return True

            if (newCounter <= len(self.frames) - 1 and newCounter >= 0):
                self.frameCounter += requestAmt
                return True
            else:
                return False
        else:
            if requestAmt == 1:
                self.frameCounter += requestAmt
                return True
            else:
                return False

    def setWriteAndAdvance(self, bWriteAndAdvance):
        ''' if outputFacotry has written out a frame in lines above,
            set this to True to allow queryNewFrame to advance a frame.
        '''
        self.writeAndAdvance = bWriteAndAdvance
    
    def queryNewFrame(self):
        
        if self.playOn:
            return self.deltaCounter(1, bypassValidation=True)
        
        if self.advanceFrame or self.writeAndAdvance:
            self.advanceFrame = False
            self.writeAndAdvance = False
            return self.deltaCounter(1)
            
        if self.retreatFrame:
            self.retreatFrame = False
            return self.deltaCounter(-1)

        if self.rewindCmd:
            self.rewindCmd = False
            return self.deltaCounter(-10)

        if self.fastforwardCmd:
            self.fastforwardCmd = False
            return self.deltaCounter(10)
            
        return False

    def _validCurrentFrame(self):
        if self.frameCounter < 0:
            return False
        if self.frameCounter > len(self.frames) - 1:
            return False
        return True
    
    def checkWriteFrame(self):

        if self.playOn or self.advanceFrame:
            if self._validCurrentFrame():
                return True
        return False

    def getFailedLoad(self):
        return self.failedLoad


class TimeFactory:

    ''' Track frametime-log's sync with FrameFactory and video-display-time. '''
    
    def __init__(self):
        self.b_delay = False
        self.t_0 = 0
        self.switchAdvanceTime = False
        self.advanceTime = 0
        self.advanceTimeT0 = 0
        self.pauseT0 = 0
        self.pauseTime = 0
        self.play = True
        self.cumtime = None
        self.frameCurrent = 0
        self.anyDelaySecs = 0.0
        self.delaySecs = 0.0
        self.delaySecsScoring = 0.5
        self.avgFps = 0.0
        self.avgFrametime = 0.0

    def setFrametimeLog(self, logPathFn):
        try:
            self.cumtime = TimeLog().get_cum_time(logPathFn) #[1:]
        except:
            self.cumtime = None

        try:
            self.avgFps = TimeLog().get_avg_frametime(logPathFn, b_hz=True)
            self.avgFrametime = TimeLog().get_avg_frametime(logPathFn, b_hz=False)
        except:
            self.avgFps = None
            self.avgFrametime = None


    def setDelay(self, b_delay):
        self.b_delay = b_delay

    def setDelaySecs(self, delaySecs):
        self.delaySecs = float(delaySecs)

    def setScoringDelaySecs(self, scoringDelaySecs):
        self.delaySecsScoring = scoringDelaySecs

    def setT0(self):
        self.t_0 = time.time()
    
    def setFrameCurrent(self, frameCurrent):
        self.frameCurrent = frameCurrent

    def getCumFrametimeArray(self):
        return copy.copy(self.cumtime)

    def _validCumTime(self):
        if self.cumtime is None:
            return False
        if len(self.cumtime) == 0:
            return False
        return True

    def _validCurrentFrame(self):
        if self.frameCurrent < 0:
            return False
        if self.frameCurrent >= len(self.cumtime):
            return False
        return True

    def cumTimeCurrent(self):
        if not(self._validCumTime()):
            return -1
        if not(self._validCurrentFrame()):
            return -1
        return self.cumtime[self.frameCurrent]

    def cumTimeTotal(self):
        if not(self._validCumTime()): 
            return -1
        return self.cumtime[len(self.cumtime) - 1]

    def avgFrameFps(self):
        return (self.avgFps, self.avgFrametime)

    def getFrametimeCurrent(self):
        return self.cumtime[self.frameCurrent]

    def getLagtimeCurrent(self):
        
        if not(self._validCumTime()) or not(self._validCurrentFrame()):
            return 0

        if self.frameCurrent == 0:
            return 0
        else:
            return self.cumtime[self.frameCurrent] - self.cumtime[self.frameCurrent - 1]


    def lagTuple(self):
        
        if not(self._validCumTime()) or not(self._validCurrentFrame()):
            return (-1, -1)
        
        _lag0 = -1 if (self.frameCurrent < 1) else 0
        _lag1 = -1 if (self.frameCurrent > len(self.cumtime) - 2) else 0
        
        if _lag0 != -1:
            _lag0 = self.cumtime[self.frameCurrent] - self.cumtime[self.frameCurrent - 1]
        if _lag1 != -1:
            _lag1 = self.cumtime[self.frameCurrent + 1] - self.cumtime[self.frameCurrent]        
        
        return (_lag0, _lag1)
        

    def setPlay(self, playOn, advanceOn):
        if self.play == playOn: 
            pass
        else:
            
            if self.switchAdvanceTime:
                self.pauseTime -= self.advanceTime
                self.switchAdvanceTime = False
            
            if playOn == False:
                self.pauseT0 = time.time()
            if playOn == True:
                self.pauseTime += (time.time() - self.pauseT0)
            self.play = playOn
            
        if advanceOn:
            if not(self.switchAdvanceTime):
                self.switchAdvanceTime = True
                try:
                    self.advanceTimeT0 = self.cumtime[self.frameCurrent]
                except:
                    self.advanceTimeT0 = 0

    def setScoringDelay(self, bScoringData, bShowScoring):
        if not(bScoringData) or not(bShowScoring):
            self.anyDelaySecs = self.delaySecs
        else:
            self.anyDelaySecs = self.delaySecsScoring

    def accumAdvanceTime(self):
        ''' this offsets pauseTime by including lapsed time of frames seen thru
            advanceFrame (instead of thru play); still not exactly right.'''
        if self.switchAdvanceTime:
            try:
                self.advanceTime = self.cumtime[self.frameCurrent] - self.advanceTimeT0
            except:
                self.advanceTime = 0

    def delayFrame(self):
        ''' sleep in frame loop to match cumtime '''

        if not(self.play): return
        
        if not(self._validCumTime()): return
        if not(self._validCurrentFrame()): return
        
        if self.anyDelaySecs > 0.001:
            time.sleep(self.anyDelaySecs)
            self.pauseTime += self.anyDelaySecs
            return

        if not(self.b_delay): return

        secsAhead = ( self.cumtime[self.frameCurrent] 
                        - 
                      (time.time() - (self.pauseTime + self.t_0))
                    )

        if secsAhead > 0.001:
            time.sleep(secsAhead - 0.001)

        return 
        
class DirectoryFactory:

    ''' Handle directory path and video-file selection and rotation'''

    def __init__(self):
        self.playCounter = 0
        self.b_play_dir = False
        self.initDir = ""
        self.fn = ""
        self.listVids = None


    def setRunType(self, b_play_dir = False):
        self.b_play_dir = b_play_dir

    def setData(self, initDir, fn=""):
        
        self.initDir = initDir

        if not(self.b_play_dir):
            self.fn = fn
        
        if self.b_play_dir:

            vidExts = (".avi",)
            
            listFiles = os.listdir(self.initDir)
            
            self.listVids = filter(lambda fn: 
                                    any([ext in fn for ext in vidExts])
                                  ,listFiles)

    def vidFn(self):

        if self.b_play_dir:
            if len(self.listVids) == 0:
                vidFn = ""
            else:
                vidFn = self.listVids[self.playCounter % len(self.listVids)]
        else:
            vidFn = self.fn
        
        return vidFn
    
    def vidPathFn(self):

        vidFn = self.vidFn()

        return os.path.join(self.initDir, vidFn)

    def frametimePathFn(self):

        _vidFn = self.vidFn()
        _frametimeFn = ".".join(_vidFn.split(".")[:-1])
        _frametimeFn += ".txt"
        
        return os.path.join(self.initDir, _frametimeFn)

    
    def metalogPathFn(self):

        _vidFn = self.vidFn()
        _metalogFn = ".".join(_vidFn.split(".")[:-1])
        _metalogFn += ".metalog"
        
        return os.path.join(self.initDir, _metalogFn)

    def checkExit(self, bFailedLoad):
        ''' return True to exit from outermost loop; exit program'''        

        if bFailedLoad:
            if not(self.b_play_dir):
                print 'Exiting: video file not able to be opened.'
                return True
        
        if self.b_play_dir:
            if len(self.listVids) < 1:
                print 'Exiting: failed to find video files in this directory'
                return True
        
        return False

    def incrementPlayCounter(self):
        self.playCounter += 1


class OutputFactory:

    ''' Handles logic for outputting a video '''

    def __init__(self):
        self.outputDir = ""
        self.vidwriter = None
        self.timewriter = None
        self.metawriter = None
        self.writeVidFn = None
        self.writeTimeFn = None
        self.writeMetaFn = None
        self.bWriteVidOn = False
        self.bWriteFrameCmd = False
        self.bWriteFrameSnap = False
        self.bWriteScoreSnap = False
        self.bAllowDuplicates = False
        self.bInitWriteVid = False
        self.advanceFrame = False
        self.compressionEnum = 0
        self.framesData = []
        self.framesInd = []
        self.frameCounter = None


    def setOutputDir(self, outputDir):
        self.outputDir = outputDir
    
    def resetFramesData(self):
        self.framesData = []

    def resetFramesInd(self):
        self.framesInd = []
        self.frameCounter = None

    def setCmd( self
                ,duplicatesEnum=None
                ,initWriteVid=None
                ,compressionEnum=None
                ,writevidOn=None
                ,switchWriteFrame=None
                ,switchWriteScoring=None
                ,switchOverideNote=None
                ):
        
        if duplicatesEnum is not None:
            self.bAllowDuplicates = True if duplicatesEnum == 1 else False

        if initWriteVid:
            self.bInitWriteVid = True
            g.initWriteVid = False
        else:
            self.bInitWriteVid = False

        if compressionEnum is not None:
            self.compressionEnum = compressionEnum

        if writevidOn is not None:
            self.bWriteVidOn = writevidOn

        self.advanceFrame = False
        
        if switchWriteFrame is not None:
            self.bWriteFrameSnap = switchWriteFrame
            if switchWriteFrame:
                g.switchWriteVid = False
                self.advanceFrame = True
                

        if switchWriteScoring is not None:
            self.bWriteScoreSnap = switchWriteScoring
            if switchWriteScoring:
                g.switchWriteScoring = False
                self.advanceFrame = True

        if switchOverideNote is not None:
            self.bWriteOverideSnap = switchOverideNote
            if switchOverideNote:
                g.switchOverideNote = False
                self.advanceFrame = True


    def getAdvanceFrame(self):
        return self.advanceFrame

    def checkWriteVid(self):
        return self.bInitWriteVid
    
    def setWriteFrameCmd(self, bWriteFrame):
        self.bWriteFrameCmd = bWriteFrame

    def setFrameCounter(self, iFrameCounter):
        self.frameCounter = iFrameCounter
    
    def checkDuplicateFrame(self):
        ''' return True if not duplicate / "already in output" '''
        if self.frameCounter not in self.framesInd:
            self.framesInd.append(self.frameCounter)
            return True
        else:
            return False


    def isDuplicate(self):
        ''' return False if it's not-duplicate or you allow duplicates '''
        if self.bAllowDuplicates:
            return False
        else:
            if self.checkDuplicateFrame():
                return False
            else:
                return True

    def checkWriteFrame(self):
        if ((self.bWriteVidOn and self.bWriteFrameCmd)
            or self.bWriteFrameSnap or self.bWriteScoreSnap
            or self.bWriteOverideSnap):
            
            return True
        return False

    def needScore(self):
        ''' return true if this frames notes should include scoring '''
        return self.bWriteScoreSnap

    @staticmethod
    def stripExt(fn):
        return ".".join(fn.split(".")[:-1])
    
    def initVidWriter(self, frameSize, vidFn):

        ext = "avi"
        fourcc = "h264"
        if self.compressionEnum == 1:
            fourcc = 0      #request lossless encoding
        
        if self.vidwriter is not None:
            self.vidwriter.release()
            self.vidwriter = None

        fnBase = self.stripExt(vidFn)
        
        self.writeVidFn = uniqueFn(  fn_base = fnBase + ".proc"
                                    ,fn_dir = self.outputDir
                                    ,fn_ext = ext
                                    )
            
        self.vidwriter = VidWriter( 
                             savefn = os.path.join(self.outputDir, self.writeVidFn)
                            ,fourcc = fourcc
                            ,outshape = frameSize
                            )
        
        if self.timewriter is not None:
            self.timewriter.close()
            self.timewriter = None
        
        self.writeTimeFn = self.stripExt(self.writeVidFn) + ".txt"
        
        self.timewriter = open(os.path.join(self.outputDir, self.writeTimeFn), 'w')


        self.writeMetaFn = self.stripExt(self.writeVidFn) + ".metalog"

        _f = open(os.path.join(self.outputDir, self.writeMetaFn), 'w')
        _f.close()
        self.metawriter = True

    def getWritevidFn(self):
        return self.writeVidFn

    def writeFrame(self, frame, timelogEntry, baseNote, frameData):
        ''' on advance or play, write previous frame '''

        _bDuplicate = self.isDuplicate()

        if self.vidwriter is not None and not(_bDuplicate):
        
            self.vidwriter.write(frame)

        if self.timewriter is not None and not(_bDuplicate):
            
            self.timewriter.write(str(timelogEntry) + "\n")

        if self.metawriter is not None:
            
            # overwrite existing framenote. only for new score; other 
            # framenote attr are not updated. to update other framenote
            # attr's use a new output.
            if _bDuplicate:
                
                try:
                    currentFrameData = self.framesData[self.frameCounter]
                except:
                    currentFrameData = {}
                
                #TODO-SS
                if (currentFrameData.get('scoring', None) is not None
                    and frameData.get('scoring', -1) in (None, -1)):
                    
                    # The problem here is frameData is already populated with score
                    # before this function, we want score as a separate arg here

                    # if there's already a score, don't update this record
                    return 

                else:
                    try:
                        self.framesData[self.frameCounter] = frameData
                    except:
                        self.framesData.append(frameData)

            else:
                self.framesData.append(frameData)

            fullNotes = baseNote
            
            proc_data = fullNotes.get('proc-data', {})
            proc_data['last_write_compression_enum'] = g.compressionEnum

            fullNotes['proc-data'] = proc_data
            
            fullNotes['frames'] = self.framesData

            fullNotes = self.orderDict(copy.copy(fullNotes)
                                        ,last_keys = ["frames"])
            
            metalogEntire = json.dumps(fullNotes, indent = 4)   
            
            _f = open(os.path.join(self.outputDir, self.writeMetaFn), 'w')
            _f.truncate(0)
            _f.write(metalogEntire)
            _f.close()

    @staticmethod
    def orderDict(dict, first_keys= [],  last_keys = []):
            
        _keys = [k for k in dict.keys()]
        _order = [0 for _ in range(len(_keys))]
        
        for i in range(len(_keys)):
            if _keys[i] in first_keys: 
                _order[i] = -1
            if _keys[i] in last_keys: 
                _order[i] = 1
        
        _temp = [(a,b) for a,b in zip(_keys,_order)]
        _temp.sort(key=lambda tup: tup[1])
        
        sorted_keys = [elem[0] for elem in _temp]
        
        output = OrderedDict()
        for k in sorted_keys:
            output[k] = dict[k]
        
        return output


class NotesFactory:

    ''' handle non-timelog data associated with each video, and and each frame '''

    def __init__(self):
        self.metalog = MetaDataLog()
        self.vidIsLoaded = False
        self.isProcessed = False
        self.dataVid = {}
        self.frameNoteFailed = False
        
        self.orientation = 0
        self.compression = -1

        self.bOverideFramenote = False
        self.framesDataExisting = []
        self.frameInd = None
        self.frameScoring = ScoreSchema()   #Legacy-SS
        self.displayFrameScoring = ScoreSchema()
        
        self.frameLogInputPathFn = None
        self.defaultLogFrameInputPathFn = "notes/guiview.jsonc"
        self.defaultFrameNotePathFn = "notes/framenote.json"
        self.defaultFrameNoteOveridePathFn = "notes/framenote-override.jsonc"
        

    def setFrameLogInput(self, frameLogPathFn):
        ''' set the path to framelog input which is json template for creation
            of frameData-dict'''

        if frameLogPathFn == "":
            self.frameLogInputPathFn = self.defaultLogFrameInputPathFn
        else:
            self.frameLogInputPathFn = frameLogPathFn

        try:
            _f = open(self.frameLogInputPathFn, 'r')
            _f.close()
        except:
            print 'couldnt open frameLogInput at: ', frameLogPathFn
            self.frameLogInputPathFn = None

    
    def setFrameCurrent(self, frameInd):
        self.frameInd = frameInd
    
    def setScoring(self, scoringData):
        self.frameScoring.addCircle(scoringData)

    def setDisplayScoring(self, scoringData):
        self.displayFrameScoring.load(scoringData)

    def getOrientation(self):
        return self.orientation   #degrees clockwise

    def getCompression(self):
        if self.compression == 0:   # this is the code for lossless
            return 1    
        return 0

    def getBallColor(self):
        try:
            return self.dataVid['notes']['details']['ball_color']
        except:
            return None

    def setCmd(self
                ,switchOverideNote=None
                ):
        
        if switchOverideNote is not None:
            self.bOverideFramenote = switchOverideNote
            # note: still need to read this below in 
            # output.setCmd, don't alter global here.

    def loadMetaLog(self, metalogPathFn):
        
        try:
            self.dataVid  = self.metalog.get_log_data(metalogPathFn)
            
            self.orientation = self.dataVid.get('notes', 0).get('orientation', 0)

            self.compression = self.dataVid.get('fourcc_enum', -1)
            
            if isinstance(self.metalog.data, dict):
                if len(self.metalog.data.keys()) > 0:
                    self.vidIsLoaded = True

            if self.dataVid.get('processed', False):
                self.isProcessed = True
                self.loadFrameNotes()
            else:
                self.dataVid['processed'] = True
                self.dataVid['proc-data'] = {}  #e.g. datetime of processing
        
        except:
            self.dataVid = {}

    def loadFrameNotes(self):
        ''' if video is processed it already has frame notes, load those '''
        try:
            assert len(self.dataVid['frames']) > 0
            assert isinstance(self.dataVid['frames'][0], dict)
            self.framesDataExisting = self.dataVid['frames']
        except:
            self.framesDataExisting = []

    def getFrameNoteCurrent(self):
        ''' return a dict representing frame data '''
        try:   return self.framesDataExisting[self.frameInd]
        except: return {}

    
    def getFrameScoreCurrent(self):
        ''' return the score or None. '''
        try:
            objScoring = ScoreSchema()
            objScoring.load(self.getFrameNoteCurrent().get('scoring', None))
            return objScoring.getAll()
        except:
            return None

    def checkFrameHasScore(self):
        ''' return True is there's anything stored in framenote.scoring '''
        return self.getFrameNoteCurrent().get('scoring', None) is not None

    def getFrameType(self):
        try:
            frameNote = self.getFrameNoteCurrent()
            return frameNote['frame_type']
        except:
            return None
    
    def getFrameScoreForTrack(self):
        ''' returns relevant params from metalog to tracking module '''
        try:
            return self.getFrameType(), self.getFrameScoreCurrent(b_bypass=True)
        except:
            return None, None

    def loadFrameLogCurrent(self):
        ''' load data from notepad '''
        if self.frameLogInputPathFn is not None:
            try:
                with open(self.frameLogInputPathFn, "r") as f:
                    lines = f.readlines()
                input_str = ''.join(lines)
                
                #remove comments
                input_str = re.sub(r'\\\n', '', input_str)      
                input_str = re.sub(r'//.*\n', '\n', input_str)
        
                return json.loads(input_str)
            except:
                print 'couldnt parse framelog jsonc'
                return {}
        else:
            return {}
    
    def outputFrameNote(self):
        ''' write out current frame note into a text file; edit if needed'''
        if not(self.isProcessed):
            return
        try:
            with open(self.defaultFrameNotePathFn, 'w') as f:
                json.dump(self.getFrameNoteCurrent(),f, indent = 4)
            
            self.frameNoteFailed = False

        except:
            self.frameNoteFailed = True

    def loadFrameNoteInput(self):
        ''' read in frame note input, this will absorb any edits you made'''
        if not(self.isProcessed):
            return
        try:
            with open(self.defaultFrameNotePathFn, 'r') as f:
                lines = f.readlines()
            lines = "".join(lines)

            frameNote = json.loads(lines)
            return frameNote
        except:
            return self.getFrameNoteCurrent()

    def loadFramenoteOveride(self):
        if not(self.isProcessed):
            return
        try:
            with open(self.defaultFrameNoteOveridePathFn, 'r') as f:
                lines = f.readlines()
            lines = "".join(lines)

            lines = re.sub(r'\\\n', '', lines)      
            lines = re.sub(r'//.*\n', '\n', lines)
            
            return json.loads(lines)
        except:
            print 'failed to load ', str(self.defaultFrameNoteOveridePathFn)
            return {}



    def getFrameData(self):
        ''' Return frameData. If no existing data, create new frameData-dict. If 
            frameData already exists and was loaded; there are multiple opportunites
            to update/add/delete the existing data here, based on gui-cmd's and
            editing files in an editor. Data is ultimately consumed by output.
        '''

        if self.isProcessed:

            if not(self.frameNoteFailed):
                #override any param for this frame in notepad
                frameData = self.loadFrameNoteInput()
            else:
                #couldnt find/open txt file; keep the same
                frameData = self.getFrameNoteCurrent()


            if self.displayFrameScoring.checkHasContents() is not None:

                #gui-cmd: writeFrame+Score - update scoring dict

                frameData['scoring'] = self.mergeDicts(
                                             main = frameScoring.getAll()
                                            ,update = displayFrameScoring.getAll()
                                            )

            if self.bOverideFramenote:    
                
                #gui-cmd: writeFrame+Override - add/overwrite params from notepad

                frameOveride = self.loadFramenoteOveride()
                frameData = self.mergeDicts(main=frameData, update=frameOveride)
        
        else:

            #frameData is new; load the framedata from txt file
            frameData = self.loadFrameLogCurrent()
            
            frameData['orig_vid_index'] = self.frameInd

            frameData['scoring'] = self.displayFrameScoring.getAll()

        return frameData

    def getBaseNote(self):
        
        baseNote = copy.deepcopy(self.dataVid)
        try:
            del baseNote['frames']
        except:
            pass  #some metalogs don't have frames
        assert 'frames' not in baseNote.keys()
        return baseNote

    def getBaseFrameNote(self, frameNote):
        
        baseFrameNote = copy.deepcopy(frameNote)
        try:
            del baseFrameNote['scoring']
        except:
            pass  #some frameNotes don't have scoring
        assert 'scoring' not in baseFrameNote.keys()
        return baseFrameNote

    
    @classmethod
    def mergeDicts(cls, main, update):
        ''' with terminal nodes in update(dict) overwrite the value at those
            nodes in main(dict) if they exist:
                main:   {"a": 1, "b": 2, "inner": {"z":1}} 
                update: {"b":99, "inner":{"z": -99}}
                ->     {"a": 1, "b": 99, "inner":{"z": -99}}
            (main should have updates and adds but never deletes)
        '''

        try:
            assert isinstance(main, dict)
            assert isinstance(update, dict)
        except Exception as e:
            print e.message
            return main

        updateKeys, updateVals = cls.recurseKeys(update)
        
        newMain = cls.recurseUpdate(copy.deepcopy(main), updateKeys, updateVals)

        return  newMain
        
        

    @classmethod
    def recurseKeys(cls, inputDict):
        ''' build [nested] list for keys and vals in inputDict:
                inputDict:  {"a":1, "b":2, "c": {"c_a":17}}
                ->:         ["a", "b", ["c", "c_a"]],   [1, [None, 17], 2])
        '''
        keyList, valList = [], []

        for k in inputDict.keys():

            if isinstance(inputDict[k], dict):
                
                tmpKey, tmpVal = cls.recurseKeys(inputDict[k])
                
                nestedKey = [k]
                nestedVal = [None]

                if len(tmpKey) > 0:
                    nestedKey.extend(tmpKey)
                    nestedVal.extend(tmpVal)

                keyList.append(nestedKey)
                valList.append(nestedVal)

            else:
                keyList.append(k)
                valList.append(inputDict[k])

        return keyList, valList

    
    @classmethod
    def recurseUpdate(cls, inputDict, listKeys, listVals):

        if inputDict is None:
            return None

        for _key, _val in zip(listKeys, listVals):

            if isinstance(_key, list):
                
                _dict = cls.recurseUpdate(  
                                    copy.deepcopy(inputDict.get( _key[0], None))
                                    , _key[1:]
                                    , _val[1:]
                                    )

                inputDict[_key[0]] = _dict

            else:
                
                if inputDict.has_key(_key):
                    inputDict[_key] = _val
                else:
                    # main doesn't have that key
                    pass

        return inputDict

