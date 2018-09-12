import time
import copy

class TimeLog:
    ''' to track timing '''
    
    def __init__(self, inert=False):
        
        self.inert=inert
        self.t0 = time.time()
        self.b_init = False
        self.log_frame_time = []
        self.path_fn = ""

        self.inert=False
    
    def time_interval(self):
        
        t1 = time.time()
        t_interval = t1 - self.t0
        self.t0 = t1
        return t_interval


    def log_time(self):
        ''' add element to log_frame_time '''
        
        if self.inert: return
        
        self.log_frame_time.append(self.time_interval())

    def set_output(self, path_fn):
        ''' set path_fn by changing x/x/fn.avi to x/x/fn.txt '''
        
        if self.inert: return
        
        base = path_fn.split(".")[0]
        base += ".txt"
        self.path_fn = base
    

    def output_log(self, path_fn = ""):
        ''' write out log_frame_time to a file '''
        
        if self.inert: return
        
        if path_fn == "":
            path_fn = self.path_fn
        
        output = copy.copy(self.log_frame_time[1:])
        output = [str(x)[:6] for x in output]
        output = '\n'.join(output)

        with open(path_fn, 'w') as f:
            f.writelines(output)
        


    def load_log_file(self):
        pass

    def load_multi_log_file(self):
        pass

    def multi_interpret_log(self):
        pass
    
    def interpret_log(self, path_fn, skip_frist_n=0):
        ''' output summary stats from log '''
        f = self.load_log_file(path_fn)
        lines = f.readlines()
        f.close()
        data = map(lambda x: float(x), lines)
        data = data[sk]




