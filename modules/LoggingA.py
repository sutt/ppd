import os, sys
import Globals

class Log:

    def __init__(self):
        
        self.MSG_NO_THRESHES = False

    def log(self, inp_code):

        if inp_code == "MSG_NO_THRESHES":
            # TODO - this is a switch that only prints once, 
            # instead of each time a frame is read and proc'd.
            # Thus we need to refresh switch once error is cleared.
            print 'No thresholding booleans are set.'
            self.MSG_NO_THRESHES = True