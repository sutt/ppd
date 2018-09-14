import os
import time
import copy
from StatsUtils import print_summary_stats

class TimeLog:
    ''' to track timing '''
    
    def __init__(self, inert=False, b_log_vars=False):
        
        self.inert=inert
        self.b_log_vars = b_log_vars
        self.b_log_start = True
        self.b_sleep_schedule = False
        self.sleep_val = 0.004
        self.t0 = time.time()
        self.start_t1 = time.time()
        self.b_init = False
        self.found_first_frame = False
        self.log_frame_time = []
        self.log_start_time = []    #as diff b/w t1 and start_t1
        self.log_schema_vars = []
        self.path_fn = ""
        
        self.log_schema = [
            "data"
            ,"dataStart"
            ,"recordOn"
            ,"previewFrame"
            ,"frameSizeEnum"
        ]


    def log_time(self, *schema_vars):
        ''' add element to log_frame_time '''
        
        if self.inert: return
        
        t1 = time.time()
        self.log_frame_time.append(t1 - self.t0)
        self.t0 = t1

        if self.b_log_start:
            self.log_start_time.append(t1 - self.start_t1)
        
        if not(self.b_log_vars):
            if schema_vars[0] == True and not(self.found_first_frame):
                self.first_record_frame = len(self.log_frame_time)
                self.found_first_frame = True
        
        if len(schema_vars) > 0 and self.b_log_vars:
            self.log_schema_vars.append(schema_vars)

        if self.b_sleep_schedule:
            self.sleep_val *= 1.01
            time.sleep(self.sleep_val)

    
    def log_start(self):
        ''' log here before frame-read: at t1 as t0 was previous'''
        
        if self.inert: return
        if not(self.b_log_start): return

        self.start_t1 = time.time()

    
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
        
        #first frame is skip on sw_record_on in guirecord
        frame_ind = 1 if self.b_log_vars else self.first_record_frame + 1  
        
        output = copy.copy(self.log_frame_time[frame_ind:])
        output = [str(x)[:6] for x in output]

        if self.b_log_start:
            tmp = copy.copy(self.log_start_time[frame_ind:])
            tmp = [str(x)[:6] for x in tmp]
            output = [a + "," + b for a,b in zip(output, tmp)]
        
        if len(self.log_schema_vars) > 0:
            
            schema_vars = copy.copy(self.log_schema_vars)
            schema_vars = map(lambda tup: ",".join(map(lambda elem: str(elem)
                                                        , tup)
                                                    )
                                        , schema_vars)

            output = [a + "," + b for a,b in zip(output, schema_vars)]
        
        output = '\n'.join(output)

        with open(path_fn, 'w') as f:
            f.writelines(output)

        self.log_frame_time = []
        self.log_start_time = []
        self.log_schema_vars = []

        
    def load_log_file(self, path_fn):
        ''' load file, return data as 1-string per line'''
        with open(path_fn, 'r') as f:
            s_data = f.readlines()
        return s_data

    def load_log_data(self, path_fn):
        ''' return the data from the log file '''

        s_data = self.load_log_file(path_fn)
        
        s_data = map(lambda s: s.strip(), s_data)
        sep_data = map(lambda s: s.split(","), s_data)
        
        data = []
        for elem in sep_data:
            tmp = [float(elem[0])]
            tmp.extend(elem[1:])
            data.append(tmp)

        return data

    def filter_data(self, data, schema_var, val):
        ''' return only data that fits the params 
                data: list of list
                schema_var: str (within self.log_schema)
                val: str        (e.g "True")    
        '''
        
        var_ind = self.log_schema.index(schema_var)
        
        tmp = filter(lambda tup: tup[var_ind] == val, data)
        
        return tmp



    def load_multi_log_file(self):
        pass

    def multi_interpret_log(self):
        pass
    
    def interpret_log(  self
                        ,path_fn
                        ,skip_first_n=0
                        ,b_hz=False
                        ,filter_schema_var=""
                        ,filter_schema_val=None
                        ,b_start_time=False
                        ):
        ''' output summary stats from log '''
        
        data = self.load_log_data(path_fn)

        if filter_schema_var != "":
            
            data = self.filter_data(data
                                   ,schema_var = filter_schema_var
                                   ,val = filter_schema_val
                                   )

        data = data[skip_first_n:]

        data = [x[0] for x in data]

        if b_hz:
            data = map(lambda x: 1/x, data)
        
        head, tail = os.path.split(path_fn)
        print '-----------'
        print 'metric:  %s' % ('FPS' if b_hz else 'time-per-frame')
        print 'file:    %s' % tail

        if skip_first_n > 0:
            print 'skip:    %i' % skip_first_n
        
        if filter_schema_var != "":
            print 'filter   %s = %s' % (filter_schema_var, str(filter_schema_val))

        print '-----------'
        
        print_summary_stats(data)

        if b_start_time:
            pass
        




