import os
import argparse
from modules.Utils import TimeLog

ap = argparse.ArgumentParser()
ap.add_argument("--file", default="data/sept2018/misc/output1.txt")
ap.add_argument("--skip",  default=1)
ap.add_argument("--hz",  action="store_true", default=False)
ap.add_argument("--filtervar", default="")
ap.add_argument("--filterval", default="")
args = vars(ap.parse_args())

timelog = TimeLog()

timelog.interpret_log(
                       path_fn =            args["file"]
                      ,skip_first_n =       int(args["skip"])
                      ,b_hz =               args["hz"]
                      ,filter_schema_var =  args["filtervar"]
                      ,filter_schema_val =  args["filterval"]
                    )

#TODO - add tests

def test_two_basic_output_files():
    ''' test these two vid time-per-frame mean are within each other CI '''
    pass