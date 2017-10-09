import argparse

ap = argparse.ArgumentParser()
ap.add_argument("--refresh", type=int, default=1)
ap.add_argument("--defaultFalse", action = "store_true") #, \
                                    #dest='feature')
                                 # default=False)
ap.add_argument("--defaultTrue", action="store_false" ) # , \
                                    #dest='feature')
ap.set_defaults(feature=False)
                                 #default=True)

args = vars(ap.parse_args())

if args["defaultFalse"]:
    print ' regular defaultFalse'

if args["defaultTrue"]:
    print ' regular defaultTrue'

if bool(args["defaultFalse"]):
    print ' bool defaultFalse'

if bool(args["defaultTrue"]):
    print ' bool defaultTrue'