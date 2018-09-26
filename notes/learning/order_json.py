from collections import OrderedDict
import json


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
fullNotes = self.orderDict(fullNotes, last_keys = ["frames"])

if __name__ == "__main__":
    
    
    d = {"z": 99, "a":2, "c": "val"}
    print json.dumps(d)
    
    out = orderDict(d)
    print json.dumps(out)