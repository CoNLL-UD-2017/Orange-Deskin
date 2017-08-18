#!/usr/bin/env python
# -*- coding: UTF8 -*-


# parse /media/training-datasets/universal-dependency-learning/conll17-ud-development-2017-03-19/metadata.json"

# run (./tira.py  inputdataset outputdir)
#   ./tira.py  /data/SemanticData/conll2017/test/final/ud-test-v2.0-conll2017/input/conll17-ud-test-2017-05-09 out2

# run eval (conll17_tira_eval.py [-h] truth system output)
#   cd /data/SemanticData/conll2017/test/final/ud-test-v2.0-conll2017
#  ./evaluation_script/conll17_tira_eval.py  gold/conll17-ud-test-2017-05-09/ /users/jeuh6401/conll2017/Orange-Deskin/out2 test1/ > res6.txt



import json
import sys
import os

class RunTest:
    def __init__(self, inputdataset, outputdir):
        mydir = os.path.dirname(os.path.realpath(sys.argv[0]))    
    
        ifp = open("%s/metadata.json" % inputdataset)
        objects = json.load(ifp)
        
        number_of_lgs = len(objects)
        ctlg = 0
        # we read the json file and process all languages in there
        # we write the result file to outputdir
        for object in objects:
            ctlg += 1
            lcode = object[u"lcode"]
            ltcode = object[u"ltcode"]
            psegmorfile = object[u"psegmorfile"] # XX-udpipe.conllu
            outfile = object[u"outfile"]            
            goldfile = object[u"goldfile"]
            
            if True: #ltcode == u"tr":
                print "Running %d/%d: %s" % (ctlg, number_of_lgs, ltcode)
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
        
