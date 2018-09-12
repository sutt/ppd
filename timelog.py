import os
import argparse
from modules.Utils import TimeLog

ap = argparse.ArgumentParser()
ap.add_argument("--file", default="data/sept2018/misc/output1.txt")
ap.add_argument("--skip",  default=1)
args = vars(ap.parse_args())

timelog = TimeLog()

timelog.interpret_log(
                      path_fn = args["file"]
                      ,skip_frist_n=int(args["skip"])
                    )
