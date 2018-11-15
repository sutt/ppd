import os
import argparse
from modules.Utils import TimeLog
from miscutils import parseCommas
from matplotlib import pyplot as plt

def showGraph(data):
  plt.plot(data)
  plt.show()

ap = argparse.ArgumentParser()
ap.add_argument("--file", default="data/sept2018/misc/output1.txt")
ap.add_argument("--skip",  default=1)
ap.add_argument("--xrange",  default="")
ap.add_argument("--hz",  action="store_true", default=False)
ap.add_argument("--graph",  action="store_true", default=False)
ap.add_argument("--filtervar", default="")
ap.add_argument("--filterval", default="")
args = vars(ap.parse_args())

timelog = TimeLog()

timelog.interpret_log(
                       path_fn =            args["file"]
                      ,skip_first_n =       int(args["skip"])
                      ,x_range =            parseCommas(args["xrange"], bInt=True)
                      ,b_hz =               args["hz"]
                      ,filter_schema_var =  args["filtervar"]
                      ,filter_schema_val =  args["filterval"]
                    )

if args["graph"]:
  data = timelog.load_log_data(path_fn=args["file"])
  
  if args["xrange"] != "":
    x_range = parseCommas(args["xrange"])
    if x_range is not None:
      if len(x_range) == 2:
        data = data[x_range[0]:x_range[1]]
        
  showGraph(data)



#TODO - add tests

def test_two_basic_output_files():
    ''' test these two vid time-per-frame mean are within each other CI '''
    pass


