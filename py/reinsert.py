#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-

# reinsert lines deleted from conll input (since our systems does not like
# lines like "2-3 ..." or "2.1 ..." nor comment lines


import sys
import re

class Reinsert:
    def __init__(self, originalFile, parserOutput):
        orig = open(originalFile)
        parser = open(parserOutput)

        ofp = sys.stdout

        ignored = re.compile("^[0-9]+[\.-]")
        
        origline = orig.readline()
        parserline = parser.readline()

        pact = 1
        orct = 1
        while True:
            if not origline: break
            if origline.startswith("#"):
                # comment in original file, absent in parser output
                ofp.write(origline)
                origline = orig.readline()
                orct += 1

            elif ignored.search(origline):
                # 5-6 or 5.1 found, also absent in parser output
                ofp.write(origline)
                origline = orig.readline()
                orct += 1
            else:
                o = origline.split()
                p = parserline.split()

                if o[:2] != p[:2]:
                    print >> sys.stderr, "Something odd in original:%d and parser:%d, ignoring rest" % (orct, pact)
                    ofp.write(parserline)
                    for l in parser.readlines():
                        ofp.write(l)
                    break
                else:
                    ofp.write(parserline)
                    origline = orig.readline()
                    parserline = parser.readline()
                    orct += 1
                    pact += 1
                    


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print >> sys.stderr, "programm to reinsert lines ignored by the parser (comment lines and lines starting like 2-3 or 5.1"
        print >> sys.stderr, "usage: %s original-conll-file parser-output-conll-file" % sys.argv[0]
    else:
        re = Reinsert(sys.argv[1], sys.argv[2])
