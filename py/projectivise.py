#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-


# comparer simplement deux fichier CONLL, sans compresser (comme le fait compareCONLL.py
import conllTypes
import sys
import codecs

sys.stderr = codecs.getwriter('utf-8')(sys.stderr)

if __name__ == "__main__":
    import sys

    from optparse import OptionParser

    parser = OptionParser(usage="usage: %prog [options] result.conll", description="projectivise CONLL file")
    parser.add_option("-c", dest="correct", action="store_true", default=False,  help="correct non-projective words")
    parser.add_option("-d", dest="deproj", action="store_true", default=False,  help="deprojectivese tree if possible")
    


    (options, comargs) = parser.parse_args()
    if len(sys.argv) < 2 or len(comargs) < 1:
        parser.print_help()
    else:

        if options.deproj:
            conlldoc = conllTypes.ConllDocSentencewise(comargs[0], encoding="utf-8", shift=0)
            while True:
                p = conlldoc.next()
                if len(p) == 0:
                    break
                p.deprojectivize()
                p.conllOut()
            
            
        else:
            # correct a CONLL file
            conlldoc = conllTypes.ConllDocSentencewise(comargs[0], encoding="utf-8", shift=0)
            #e = Eval(comargs[0])
            ct = 0
            ctnp = 0
            ct_not_correct = 0
            ct_corrected = 0
            ctok = 0
            #for p in e.conlldoc1.phrases:
            #efp = codecs.open("non-proj.conll", "w", "utf-8")
            while True:
                p = conlldoc.next()
                if len(p) == 0:
                    break
                ct += 1
                #p.conllOut()
                #print "%d %s" % (ct, p.txt.encode("utf-8"))

                rtc = p.isProjective()
                #print >> sys.stderr, "projective", rtc

                if options.correct:
                    if not rtc:
                        # sentence is not projective, let's reattach commas
                        ct_not_correct += 1
                        #print "KO", p
                        #p.conllOut()
                        p.makeCommasProjective(use_set=False)

                        rtc = p.isProjective()
                        #print >> sys.stderr, "commas corrected: projective", rtc
                        #p.conllOut()
                        ct = 0
                        while not rtc:
                            ct += 1
                            p.projectivize(p.unprojectiveWords)
                            rtc = p.isProjective()
                            #print >> sys.stderr, "projectivised: projective", rtc
                            if ct > 4:
                                print >> sys.stderr, "to many projectivity errors in sentence %d" % ct
                            #break
                        #p.conllOut()

                        #rtc = p.isProjective()
                        #print >> sys.stderr, "projectivised: projective", rtc

                        if not p.isTree() or not rtc:
                            #print >> sys.stderr, "not a tree projective"
                            #p.conllOut(efp)
                            # ne pas sortir les phrases qui reste non-projectives
                            #for x in p.unprojectiveWords:
                            #    print "\t%d: %s" % (x.ident, x.form.encode("utf-8"))
                            pass
                            continue

                        #print "OK"
                        #p.conllOut()
                        ct_corrected += 1
                    ctok += 1
                    p.conllOut()

                else:
                    if ct % 10000 == 0:
                        print "%d sentences read" % ct
                    if not rtc:
                        ctnp += 1
                        print "sentence %d not projective '%s'" % (ct, p.txt)
                        for x in p.unprojectiveWords:
                            print "\t%d: %s" % (x.ident, x.form)
            #efp.close()
            sys.stderr.write("ct:%d not_correct:%d corrected:%d, ok:%d\n" % (ct, ct_not_correct, ct_corrected, ctok))
            if ctnp:
                print "%d/%d sentences non projective (%.2f%%)" % (ctnp, ct, 100.0*ctnp/ct)

