from optparse import OptionParser

#WITHCPOS=True
#if WITHCPOS:
#	from arc_hybrid_withCPOS import ArcHybridLSTM
#else:
#	from arc_hybrid_dynet import ArcHybridLSTM
#	#from arc_hybrid import ArcHybridLSTM

import pickle, utils, os, time, sys

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("--train", dest="conll_train", help="Annotated CONLL train file", metavar="FILE", default="../data/PTB_SD_3_3_0/train.conll")
    parser.add_option("--dev", dest="conll_dev", help="Annotated CONLL dev file", metavar="FILE", default="../data/PTB_SD_3_3_0/dev.conll")
    parser.add_option("--test", dest="conll_test", help="Annotated CONLL test file", metavar="FILE", default="../data/PTB_SD_3_3_0/test.conll")
    parser.add_option("--params", dest="params", help="Parameters file", metavar="FILE", default="params.pickle")
    parser.add_option("--extrn", dest="external_embedding", help="External embeddings", metavar="FILE")
    parser.add_option("--extrnT",  action="store_true", dest="external_embedding_Textual", help="External embeddings are textual", default=False)
    parser.add_option("--extrnFilter", dest="external_embedding_filter", help="External embeddings to filter", metavar="FILE")
    parser.add_option("--extrnFilterNew", dest="external_embedding_filter_new", help="External embeddings not seen during training to filter", metavar="FILE")
    parser.add_option("--useroot",  action="store_true", dest="use_root", help="Add pseudo word *root* to sentence", default=False)
    parser.add_option("--model", dest="model", help="Load/Save model file", metavar="FILE", default="barchybrid.model")
    parser.add_option("--wembedding", type="int", dest="wembedding_dims", default=100)
    parser.add_option("--pembedding", type="int", dest="pembedding_dims", default=25)
    parser.add_option("--rembedding", type="int", dest="rembedding_dims", default=25)
    parser.add_option("--epochs", type="int", dest="epochs", default=30)
    parser.add_option("--hidden", type="int", dest="hidden_units", default=100)
    parser.add_option("--hidden2", type="int", dest="hidden2_units", default=0)
    parser.add_option("--k", type="int", dest="window", default=3)
    parser.add_option("--lr", type="float", dest="learning_rate", default=0.1)
    parser.add_option("--outdir", type="string", dest="output", default="")
    parser.add_option("--outfile", type="string", dest="outfile", default="test_predBIST.conll")
    parser.add_option("--activation", type="string", dest="activation", default="tanh")
    parser.add_option("--lstmlayers", type="int", dest="lstm_layers", default=2)
    parser.add_option("--lstmdims", type="int", dest="lstm_dims", default=200)
    parser.add_option("--cnn-seed", type="int", dest="seed", default=7)
    parser.add_option("--dynet-seed", type="int", dest="seed", default=7)
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


    (options, args) = parser.parse_args()



    global WITHCPOS
    WITHCPOS=options.WITHCPOS
    if WITHCPOS:
	from arc_hybrid_withCPOS import ArcHybridLSTM
    else:
 	if options.WITHDYNET:
	    from arc_hybrid_dynet import ArcHybridLSTM
	else:
	    from arc_hybrid import ArcHybridLSTM





    print 'Using external embedding:', options.external_embedding, "textual file:", options.external_embedding_Textual
   

    if not options.predictFlag:
	# Training
        if not (options.rlFlag or options.rlMostFlag or options.headFlag):
            print 'You must use either --userlmost or --userl or --usehead (you can use multiple)'
            sys.exit()

        print 'Preparing vocab'
	if WITHCPOS:
            words, w2i, pos, cpos, GENDER, NUMBER, PERSON, rels = utils.vocab(options.conll_train, True)
	else:
            words, w2i, pos, rels = utils.vocab(options.conll_train, False)

	#print words
	#print pos
	#print cpos

	if WITHCPOS:
            with open(os.path.join(options.output, options.params), 'w') as paramsfp:
                pickle.dump((words, w2i, pos, cpos, GENDER, NUMBER, PERSON, rels, options), paramsfp)
	else:
            with open(os.path.join(options.output, options.params), 'w') as paramsfp:
                pickle.dump((words, w2i, pos, rels, options), paramsfp)

        print 'Finished collecting vocab'

        print 'Initializing blstm arc hybrid:'
	if WITHCPOS:
	    parser = ArcHybridLSTM(words, pos, cpos, GENDER, NUMBER, PERSON, rels, w2i, options)
	else:
	    parser = ArcHybridLSTM(words, pos, rels, w2i, options)

        for epoch in xrange(options.epochs):
            print 'Starting epoch', epoch
            parser.Train(options.conll_train, epoch)
            #devpath = os.path.join(options.output, 'dev_epoch_' + str(epoch+1) + '.conll')
            devpath = os.path.join(options.output, 'dev_epoch_%03d.conll' % (epoch+1))
            utils.write_conll(devpath, parser.Predict(options.conll_dev))
	    # run evaluation
	    #command = 'perl src/utils/eval.pl -g ' + options.conll_dev + ' -s ' + devpath  + ' > ' + devpath + '.txt '
	    #print "executing: %s" % command
            #os.system(command)
	    # just show current LAS
  	    #ifp = open(devpath + '.txt')
	    #print "current LAS", ifp.readline()
            #ifp.close()

	    command = "~/bin/toolbin/conll/evaluation_script/conll17_ud_eval.py --weights ~/bin/toolbin/conll/evaluation_script/weights.clas " + options.conll_dev + "  " + devpath  + " > " + devpath + '.txt4'
	    print "executing: %s" % command
	    os.system(command)
	    # just show current LAS
  	    ifp = open(devpath + '.txt4')
	    for line in ifp.readlines():
		print line.strip()
            ifp.close()

            print 'Finished predicting dev'
            parser.Save(os.path.join(options.output, "%s_%03d" % (options.model, (epoch+1))))
    else:
	# predicting
	if WITHCPOS:
            with open(options.params, 'r') as paramsfp:
    	        words, w2i, pos, cpos, GENDER, NUMBER, PERSON, rels, stored_opt = pickle.load(paramsfp)
	else:
            with open(options.params, 'r') as paramsfp:
    	        words, w2i, pos, rels, stored_opt = pickle.load(paramsfp)
	
	print "Finished loading vocab"

	# overwrite options read from params.pickle
        stored_opt.external_embedding = options.external_embedding
	stored_opt.external_embedding_filter = options.external_embedding_filter
	stored_opt.external_embedding_filter_new = options.external_embedding_filter_new
	if WITHCPOS:
            parser = ArcHybridLSTM(words, pos, cpos, GENDER, NUMBER, PERSON, rels, w2i, stored_opt)
	else:
            parser = ArcHybridLSTM(words, pos, rels, w2i, stored_opt)

        parser.Load(options.model)
	print "model loaded", options.model
        tespath = os.path.join(options.output, options.outfile)
        ts = time.time()
        pred = list(parser.Predict(options.conll_test))
        te = time.time()
        utils.write_conll(tespath, pred)
	# run evaluation
	if False:
	    os.system('perl src/utils/eval.pl -g ' + options.conll_test + ' -s ' + tespath  + ' > ' + tespath + '.txt &')
	    # just show current LAS
	    ifp = open(tespath + '.txt')
	    print ifp.readline()
	    ifp.close()
        print 'Finished predicting test',te-ts

