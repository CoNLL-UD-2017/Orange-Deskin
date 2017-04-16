#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-


import pickle
import collections
import sys, types, optparse

class ReadParamsPicke:
    def __init__(self, picklefile):

        with open(picklefile, 'r') as paramsfp:
            #words, w2i, pos, cpos, rels, stored_opt = pickle.load(paramsfp)
            self.data = pickle.load(paramsfp)

    def out(self):
	#print len(data)
	ct = 0
	for x in self.data:
	    ct += 1
	    print "================ %d ===========" %ct
	    if type(x) == types.DictionaryType:
		iitems = x.items()
		iitems.sort()
		for k,v in iitems:
		   print "%s\t%s" % (k,v)
	    elif type(x) == types.ListType:
	        x.sort()
		for e in x:
		   print e
	    elif type(x) == collections.Counter:
		iitems = x.items()
		iitems.sort()
		for k,v in iitems:
   		   print "%s\t%s" % (k,v)
	    else:
                # options from OptsParser
		print type(x)
		print x
                #print x.external_embedding
		#print "zzz", dir(x.__class__)
		#iitems = x.items()
		#iitems.sort()
		#for k,v in iitems:
		#   print "%s\t%s" % (k,v)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        RP = ReadParamsPicke(sys.argv[1])
        if len(sys.argv) == 2:
            RP.out()
        else:
            params_options =  RP.data[4]
            print eval("params_options.%s" % sys.argv[2])
