import os
import random

''' utility functions parsing/directories used throughout'''

def parseCommas(strArg, bInt=True, bFloat=False):
    '''
        return a tuple from a string representing numbers separated by commas;
            useful for argparse 
        "1,2,3" -> (1,2,3) [ or (1.0,2.0,3.0) if bFloat]
    '''
    
    elems = strArg.split(",")
    elems = [filter(lambda char: char.isdigit(), elem) for elem in elems]
    elems = filter(lambda elem: len(elem) > 0, elems)
    
    if bInt:
        elems = map(lambda elem: int(elem), elems)
    elif bFloat:
        elems = map(lambda elem: float(elem), elems)
    
    if len(elems) > 0:
        return tuple(elems)
    else:
        return None

def parseCliList(str_input):
    '''
        #TODO-refactor DUPLICATE of parseCommas()

        parses comma separated cli arg:
            e.g. --mylist 1,2,x,3 -> "1,2,x,3" -> [1,2,3]
            (removes no int-parsable elements before return)

        input: str
        return: list of int's (or None if error)
    '''
    
    def tryInt(str_input):
        try:
            return int(str_input)
        except:
            return None
    
    try:
        assert type(str_input) == str
        split_input = str_input.split(",")
        parsed_input = map(tryInt, split_input)
        return filter(lambda num: num is not None, parsed_input)
    except:
        return None


def uniqueFn(fn_base
            ,fn_dir = None
            ,fn_ext = None
            ,method = "increment"
            ,guid_digits = 6
            ):
    ''' 
        Return a unique fn. Starts at fn_base1.ext.

        fn_base:    fn's base name  
                    different fn_base start back at fn_base1.ext
        fn_dir:     path to directory
                    (if None, uses current dir)
        fn_ext:     the extension w/o dot
                    (if None, considers all fns in dir w/o ext)
        method:     str - "increment" or "guid"
        guid_digits:int - number of chars in guid

        ----------------------------------------------------------
        fn = uniqueFn(  fn_base = "output"
                        ,fn_dir = args["savedir"]
                        ,fn_ext = args["ext"] )
    '''

    if method == "increment":
        
        i = 0
        _dir = os.getcwd() if fn_dir is None else fn_dir
        files = os.listdir(_dir)
        
        if fn_ext is None:
            def rm_ext(f):
                ind_dot = f[::-1].find(".")
                if ind_dot == -1:
                    return f
                else:
                    return f[:-(ind_dot+1)]
            files = [rm_ext(f) for f in files]
        
        while(True):
            i += 1
            fn = str(fn_base) + str(i)
            if fn_ext is not None:
                fn += "."
                fn += fn_ext 
                
            if i > 99999:
                print 'problem in uniqueFn, more than 100k files'
                return None
            elif fn in files:
                continue
            else:
                return fn
    
    if method == "guid":
        
        letters = 'abcdefghijklmnopqrstuvwxyz'
        numbers = '0123456789'
        chars = letters + numbers

        guid_base = [str( chars[
                        random.sample(range(len(chars)-1),1)[0]
                          ] )
                     for _ in range(guid_digits)
                    ]
        guid_base = "".join(guid_base)

        fn = fn_base + guid_base
        if fn_ext is not None:
            fn += "."
            fn += fn_ext

        return fn


def mean(data):
    return float(sum(data)) / float(len(data))

def sd(data):
    x_bar = mean(data)
    temp = sum(map(lambda x: (x - x_bar) ** 2, data)) 
    return (float(temp) / float(len(data) - 1)) ** 0.5

def print_summary_stats(data, _places = 4):
    
    _mean = mean(data)
    _sd = sd(data)
    _min = min(data)
    _max = max(data)
    _n = len(data)

    _min_sds = float(_mean - _min) / float(_sd)
    _max_sds = float(_max - _mean) / float(_sd)

    _minus2sd = float(_mean - (float(2*_sd)/float(_n**.5)))
    _plus2sd = float(_mean + (float(2*_sd)/float(_n**.5)))

    __mean = round(_mean, _places)
    __sd = round(_sd, _places)
    __min = round(_min, _places)
    __max = round(_max, _places)
    __min_sds = round(_min_sds, 1)
    __max_sds = round(_max_sds, 1)
    __minus2sd = round(_minus2sd, _places)
    __plus2sd = round(_plus2sd, _places)


    print 'n:       %i'             % _n
    print 'mean:    %.*f'           % (_places, _mean)
    print 'Z +/-  : %.*f - %.*f'    % (_places,_minus2sd, _places, _plus2sd)
    print 'min:     %.*f   %.*f sd' % (_places, _min, 1, _min_sds)
    print 'max:     %.*f   %.*f sd' % (_places, _max, 1, _max_sds)
    print 'sd:      %.*f'           % (_places, _sd)
    
