import os, sys, time, copy, json, re
from collections import OrderedDict
import numpy as np
import cv2
import argparse
from vidwriter import VidWriter
from miscutils import uniqueFn
from modules.Utils import TimeLog
from modules.Utils import MetaDataLog
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

    
    def queryNewFrame(self):
        
        if self.playOn:
            return self.deltaCounter(1, bypassValidation=True)
        
        if self.advanceFrame:
            self.advanceFrame = False
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
        

    def setPlay(self, playOn):
        if self.play == playOn: 
            return
        else:
            if playOn == False:
                self.pauseT0 = time.time()
            if playOn == True:
                self.pauseTime += (time.time() - self.pauseT0)
            self.play = playOn

    def setScoringDelay(self, scoringData):
        if scoringData is None:
            self.anyDelaySecs = self.delaySecs
        else:
            self.anyDelaySecs = self.delaySecsScoring


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
        self.bWriteFrameOn = False
        self.bWriteFrameCmd = False
        self.bWriteFrameSnap = False
        self.bWriteScoreSnap = False

        self.framesData = []


    def setOutputDir(self, outputDir):
        self.outputDir = outputDir
    
    def resetFramesData(self):
        self.framesData = []

    def setInitWriteVid(self, bInitWriteVid):
        if bInitWriteVid:
            g.initWriteVid = False
            return True
        return False

    def setWriteFrameOn(self, bWriteFrameOn, bSwtichWriteFrame, bSwitchWriteScoring):
        self.bWriteFrameOn = bWriteFrameOn
        self.bWriteFrameSnap = bSwtichWriteFrame
        self.bWriteScoreSnap = bSwitchWriteScoring
        if bSwtichWriteFrame:
            g.switchWriteVid = False
        if bSwitchWriteScoring:
            g.switchWriteScoring = False
    
    def setWriteFrameCmd(self, bWriteFrame):
        self.bWriteFrameCmd = bWriteFrame

    def checkWriteFrame(self):
        if ((self.bWriteFrameOn and self.bWriteFrameCmd)
            or self.bWriteFrameSnap or self.bWriteScoreSnap):
            return True
        return False

    def needScore(self):
        ''' return true if this frames notes should include scoring '''
        return self.bWriteScoreSnap

    @staticmethod
    def stripExt(fn):
        return ".".join(fn.split(".")[:-1])
    
    def initVidWriter(self, frameSize, vidFn, compressionEnum):

        ext = "avi"
        fourcc = "h264"
        if compressionEnum == 1:
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
        
        if self.vidwriter is not None:
        
            self.vidwriter.write(frame)

        if self.timewriter is not None:
            
            self.timewriter.write(str(timelogEntry) + "\n")

        if self.metawriter is not None:

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

        self.bShowScoring = False
        self.bFrameNotes = True
        self.framesData = []
        self.framesDataExisting = []
        self.frameInd = None
        self.frameScoring = None
        
        self.frameLogInputPathFn = None
        self.defaultLogFrameInputPathFn = "notes/guiview.jsonc"
        self.defaultFrameNotePathFn = "notes/framenote.json"
        

    def setFrameLog(self, frameLogPathFn):
        
        if frameLogPathFn == "":
            self.frameLogInputPathFn = self.defaultLogFrameInputPathFn
        else:
            self.frameLogInputPathFn = frameLogPathFn

        try:
            _f = open(self.frameLogInputPathFn, 'r')
        except:
            print 'couldnt open framelog'
            self.frameLogInputPathFn = None

    def resetFramesData(self):
        self.framesData = []
    
    def setFrameCurrent(self, frameInd):
        self.frameInd = frameInd

    def setShowScoring(self, bShowScoring):
        self.bShowScoring = bShowScoring
    
    def setScoring(self, scoringData):
        self.frameScoring = scoringData

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
        return self.framesDataExisting[self.frameInd]

    def getFrameScoreCurrent(self):
        ''' guiview calls this to check if there is a scoring event '''
        if not(self.bShowScoring):
            return None
        try:
            note = self.getFrameNoteCurrent()
            assert len(note['scoring']) == 4
            return note['scoring']
        except:
            return None

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



    def getFrameData(self):
        ''' return only current frameData; store all frame notes in outputFactory '''

        if self.isProcessed:

            #re-processing

            if self.frameNoteFailed:
                frameData = self.getFrameNoteCurrent()
            else:
                frameData = self.loadFrameNoteInput()
            

            # frameScoring is not None only when gui-cmd writeFrame+Data
            if self.frameScoring is not None:
                frameData['scoring'] = self.frameScoring
        
        else:
            
            #new-processing

            frameData = self.loadFrameLogCurrent()
            
            frameData['orig_vid_index'] = self.frameInd

            frameData['scoring'] = self.frameScoring

        return frameData

    def getBaseNote(self):
        
        baseNote = copy.deepcopy(self.dataVid)
        try:
            del baseNote['frames']
        except:
            #some metalogs don't have frames
            pass  
        assert 'frames' not in baseNote.keys()
        return baseNote
    