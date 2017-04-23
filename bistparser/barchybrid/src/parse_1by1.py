#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, string, time
import pickle


import time
import StringIO




# classe pour desambiguiser
class Parser:
    def __init__(self, options):

        self.options = options   
        self.WITHCPOS=options.WITHCPOS

        if self.WITHCPOS:
            from arc_hybrid_withCPOS import ArcHybridLSTM
        else:
            if options.WITHDYNET:
                from arc_hybrid_dynet import ArcHybridLSTM
            else:
                from arc_hybrid import ArcHybridLSTM



        print 'Using external embedding:', options.external_embedding
        if options.predictFlag:
            if self.WITHCPOS:
                with open(options.params, 'r') as paramsfp:
                    self.words, self.w2i, self.pos, self.cpos, self.GENDER, self.NUMBER, self.PERSON, self.rels, self.stored_opt = pickle.load(paramsfp)
            else:
                with open(options.params, 'r') as paramsfp:
                    self.words, self.w2i, self.pos, self.rels, self.stored_opt = pickle.load(paramsfp)


            self.stored_opt.external_embedding = options.external_embedding
            self.stored_opt.external_embedding_filter = options.external_embedding_filter
            self.stored_opt.external_embedding_filter_new = options.external_embedding_filter_new


            if self.WITHCPOS:
                self.arc_hybrid = ArcHybridLSTM(self.words, self.pos, self.cpos, self.GENDER, self.NUMBER, self.PERSON, self.rels, self.w2i, self.stored_opt)
            else:
                self.arc_hybrid = ArcHybridLSTM(self.words, self.pos, self.rels, self.w2i, self.stored_opt)

            self.arc_hybrid.Load(options.model)

    def parse(self, conllstring):
        #tespath = os.path.join(options.output, 'test_pred.conll')
        #ts = time.time()
        # c'est idiot, mais la classe ArcHybridLSTM veut lire d'un texte ...
	#tmpfilename = "/tmp/bisttmp.conll"
	#ifp = open(tmpfilename, "w")
	#ifp.write(conllstring)
	#ifp.close()
        #conll_gen = list(self.arc_hybrid.Predict(tmpfilename))
	conll_gen = list(self.arc_hybrid.Predict(conllstring, is_string=True))
	result = StringIO.StringIO()
        for sentence in conll_gen:
            for entry in sentence[1:]:
                result.write('\t'.join([str(entry.id), entry.form, '_', entry.cpos, entry.pos, '_', str(entry.pred_parent_id), entry.pred_relation, '_', '_']))
                result.write('\n')
            result.write('\n')
	out = result.getvalue()
	result.close()


        #te = time.time()
        #utils.write_conll(tespath, pred)


	
        #os.system('perl src/utils/eval.pl -g ' + options.conll_test + ' -s ' + tespath  + ' > ' + tespath + '.txt &')
	#print 'Finished predicting test' #,te-ts
	if len(out) < 10:
		print "INPUT", conllstring
		print "OUTPUT", out
	return out
 
class FeedConll:
    def __init__(self, parser, hugefile, outfile):
        # read conll sentence by conll sentence, parse and output
        ifp = open(hugefile)
        start = time.time()
        print "writing to %s" % outfile
        ofp = open(outfile, "w")
        self.parser = parser

        self.wordcount = 0
        self.sentencecount = 0
        line = ""
        block = []
        for line in ifp:
            line = line.strip()
            if line:
                block.append(line)
            else:
                 self.parse(block, ofp)
                 block = []
        if block:
            self.parse(block, ofp)
        end = time.time()
        ofp.close()
        ifp.close()
        sys.stderr.write("%d sentences with %d words parsed\n" % (self.sentencecount, self.wordcount))
        sys.stderr.write("total time: %s\n" % time.strftime("%H:%M:%S", time.gmtime(end-start)))
        
    def parse(self, block, outfile):
        self.wordcount += len(block)
        self.sentencecount += 1
        
        data = string.join(block, "\n")
        out = self.parser.parse(data)
        outfile.write(out)
        if (self.sentencecount % 200 == 0):
            sys.stderr.write("%d sentences with %d words parsed\n" % (self.sentencecount, self.wordcount))




    
#----------------------------------------------------------------------
if __name__ == "__main__":
  
    from optparse import OptionParser
    parser = OptionParser(usage="usage: %prog [options]")
    parser.add_option("--train", dest="conll_train", help="Annotated CONLL train file", metavar="FILE", default="../data/PTB_SD_3_3_0/train.conll")
    parser.add_option("--dev", dest="conll_dev", help="Annotated CONLL dev file", metavar="FILE", default="../data/PTB_SD_3_3_0/dev.conll")
    parser.add_option("--test", dest="conll_test", help="Annotated CONLL test file", metavar="FILE", default="../data/PTB_SD_3_3_0/test.conll")
    parser.add_option("--params", dest="params", help="Parameters file", metavar="FILE", default="params.pickle")
    parser.add_option("--extrn", dest="external_embedding", help="External embeddings", metavar="FILE")
    parser.add_option("--extrnFilter", dest="external_embedding_filter", help="External embeddings to filter", metavar="FILE")
    parser.add_option("--extrnFilterNew", dest="external_embedding_filter_new", help="External embeddings not seen during training to filter", metavar="FILE")
    parser.add_option("--model", dest="model", help="Load/Save model file", metavar="FILE", default="barchybrid.model")
    parser.add_option("--wembedding", type="int", dest="wembedding_dims", default=100)
    parser.add_option("--pembedding", type="int", dest="pembedding_dims", default=25)
    parser.add_option("--rembedding", type="int", dest="rembedding_dims", default=25)
    parser.add_option("--epochs", type="int", dest="epochs", default=30)
    parser.add_option("--hidden", type="int", dest="hidden_units", default=100)
    parser.add_option("--hidden2", type="int", dest="hidden2_units", default=0)
    parser.add_option("--k", type="int", dest="window", default=3)
    parser.add_option("--lr", type="float", dest="learning_rate", default=0.1)
    parser.add_option("--outdir", type="string", dest="output", default="results")
    parser.add_option("--outfile", type="string", dest="outfile", default="results.conll")
    parser.add_option("--activation", type="string", dest="activation", default="tanh")
    parser.add_option("--lstmlayers", type="int", dest="lstm_layers", default=2)
    parser.add_option("--lstmdims", type="int", dest="lstm_dims", default=200)
    parser.add_option("--cnn-seed", type="int", dest="seed", default=7)
    parser.add_option("--disableoracle", action="store_false", dest="oracle", default=True)
    parser.add_option("--disableblstm", action="store_false", dest="blstmFlag", default=True)
    parser.add_option("--bibi-lstm", action="store_true", dest="bibiFlag", default=False)
    parser.add_option("--usehead", action="store_true", dest="headFlag", default=False)
    parser.add_option("--userlmost", action="store_true", dest="rlFlag", default=False)
    parser.add_option("--userl", action="store_true", dest="rlMostFlag", default=False)
    parser.add_option("--predict", action="store_true", dest="predictFlag", default=False)
    parser.add_option("--cnn-mem", type="int", dest="cnn_mem", default=4096)
    parser.add_option("--dynet-mem", type="int", dest="dynet_mem", default=1024)

    parser.add_option("--withCPOS", action="store_true", dest="WITHCPOS", default=False)
    parser.add_option("--withDYNET", action="store_true", dest="WITHDYNET", default=False)

    parser.add_option("--port", type="int", dest="port", default=22222)

    (options, args) = parser.parse_args()

  

    parser = Parser(options=options)

#    fc = FeedConll(parser, options.conll_test, options.output + "/res.conll")
    fc = FeedConll(parser, options.conll_test, options.outfile)
    


