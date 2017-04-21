#!/usr/bin/env python
# -*- coding: UTF8 -*-


# parse /media/training-datasets/universal-dependency-learning/conll17-ud-development-2017-03-19/metadata.json"

import json
import sys
import os

class RunTest:
    def __init__(self, inputdataset, outputdir):
        mydir = os.path.dirname(os.path.realpath(sys.argv[0]))    
    
        ifp = open("%s/metadata.json" % inputdataset)
        objects = json.load(ifp)
        
        # we read the json file and process all languages in there
        # we write the result file to outputdir
        for object in objects:
            lcode = object[u"lcode"]
            ltcode = object[u"ltcode"]
            psegmorfile = object[u"psegmorfile"]
            outfile = object[u"outfile"]            
            goldfile = object[u"goldfile"]
            
            if True: #ltcode == u"tr":
                #print "Running", ltcode, psegmorfile, outfile
                command = "%s/make_prediction.sh %s/%s %s %s/%s" % \
                    (mydir,
                     inputdataset, psegmorfile, #goldfile, #psegmorfile, 
                     ltcode, 
                     outputdir, outfile)
                #print command
                os.system(command)
#            else:
#                command = "cp %s/%s %s/%s" % \
#                     (inputdataset, psegmorfile,
#                      outputdir, outfile)
#                #print command
#                os.system(command)
        ifp.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print >> sys.stderr, "usage: %s  inputdataset outputdir" % sys.argv[0]
    else:
        rt = RunTest(sys.argv[1], sys.argv[2])