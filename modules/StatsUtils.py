
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

    _minus2sd = float(_mean - 2*_sd)
    _plus2sd = float(_mean + 2*_sd)

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
    print '2sd +/-: %.*f - %.*f'    % (_places,_minus2sd, _places, _plus2sd)
    print 'min:     %.*f   %.*f sd' % (_places, _min, 1, _min_sds)
    print 'max:     %.*f   %.*f sd' % (_places, _max, 1, _max_sds)
    print 'sd:      %.*f'           % (_places, _sd)


    
    

