from itertools import product

'''
    Helper functions for batch changing track params.

    TODOs:
        [ ] buildGradient -> combineThreshes -> doesn't work
            for combinations with multiple indexes
            [ ] need to decompose the tuple into 
                thesh_lo_r, thesh_lo_g, etc. then recompose before
                setting trackParams
'''


def buildGradient(
          name
         ,baseline
         ,index = None
         ,delta = 5
         ,steps = 5
         ,validMin = None
         ,validMax = None
        ):
    '''
        build a gradient for variable of interest
        
        returns: list of dicts
        
            [
               {name: val_gradienT[0]}
              , ...
              ,{name: vali_gradient[steps*2 + 1]}
            ]
        
        if variable is a tuple, use 'index' arg to alter only
        this variable within the tuple, and validate on it.
        
        if validXX is not None, checks _validPoint against
        this condition to consider adding it to gradient output.
        
        TODO:
            index as list of indexes - can't be done with this function
            will need to combine dicts later on
    '''
    
    gradient = [x for x in range(-delta * steps
                                 ,delta * (steps + 1)
                                 ,delta)
               ]
    
    space = []

    for _gradient in gradient:
        
        if index is None:
            
            # scalar variables
            
            _point = baseline + _gradient
            
            _validPoint = _point
            
        else:
            
            #tuple variables
            
            _point = list(baseline)
            
            _point[index] = _point[index] + _gradient
            
            _point = tuple(_point)
            
            _validPoint = _point[index]
                        
            
        #validation
        if validMin is not None:
            if _validPoint < validMin:
                continue
                
        if validMax is not None:
            if _validPoint > validMax:
                continue
        
        space.append(_point)

    points_a = [{name:val} for val in space]
    
    return points_a


def combineDicts(*args):
    d = {}
    for elem in args:
        for k in elem.keys():
            d[k] = elem[k]
    return d

def combineGradients(listGradients):

    '''
        input: list of Gradients (which are list of dicts)
        output Gradient (list of dicts) which have all possible
            combinations of indiv. gradients in input list combined.
    '''
    
    output = []
    
    dims = [len(gradientG) for gradientG in listGradients]
    
    xdims = [range(x) for x in dims]
    
    for _p in product(*xdims):
        
        gInd = [(i,v) for i,v in enumerate(_p)]
        
        dicts = [ listGradients[_ind[0]][_ind[1]] for _ind in gInd]
        
        output.append( combineDicts(*dicts) )
        
    return output
