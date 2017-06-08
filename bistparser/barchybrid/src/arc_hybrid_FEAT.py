from pycnn import *
#from gpycnn import *
from utils import ParseForest, read_conll, write_conll
from operator import itemgetter
from itertools import chain
import utils, time, random
import numpy as np

import StringIO
import w2vread2

class ArcHybridLSTM:
    def __init__(self, words, pos, cpos, GENDER, NUMBER, PERSON, rels, w2i, options):
        self.model = Model()
        self.trainer = AdamTrainer(self.model)
        random.seed(1)

        self.activations = {'tanh': tanh, 'sigmoid': logistic, 'relu': rectify, 'tanh3': (lambda x: tanh(cwise_multiply(cwise_multiply(x, x), x)))}
        self.activation = self.activations[options.activation]

        self.oracle = options.oracle
        self.ldims = options.lstm_dims * 2
        self.wdims = options.wembedding_dims
        self.pdims = options.pembedding_dims
        self.rdims = options.rembedding_dims
        self.layers = options.lstm_layers
        self.wordsCount = words
        self.vocab = {word: ind+3 for word, ind in w2i.iteritems()}
        self.pos = {word: ind+3 for ind, word in enumerate(pos)}
        #self.cpos = {word: ind+3 for ind, word in enumerate(cpos)}
        self.GENDER = {word: ind+3 for ind, word in enumerate(GENDER)}
        self.NUMBER = {word: ind+3 for ind, word in enumerate(NUMBER)}
        self.PERSON = {word: ind+3 for ind, word in enumerate(PERSON)}
        self.rels = {word: ind for ind, word in enumerate(rels)}
        self.irels = rels

        self.headFlag = options.headFlag
        self.rlMostFlag = options.rlMostFlag
        self.rlFlag = options.rlFlag
        self.k = options.window
	#print options
	self.use_root = False #options.use_root # if true we add pseudo word *root* to sentence

        self.nnvecs = (1 if self.headFlag else 0) + (2 if self.rlFlag or self.rlMostFlag else 0)

        self.external_embedding = None
        if options.external_embedding is not None:
            #external_embedding_fp = open(options.external_embedding,'r')
            #external_embedding_fp.readline()
            #self.external_embedding = {line.split(' ')[0] : [float(f) for f in line.strip().split(' ')[1:]] for line in external_embedding_fp}
            #external_embedding_fp.close()
#	    W2V = w2vread.ReadW2V(options.external_embedding, 
#				  binary=not options.external_embedding_Textual, 
#				  filterfile=options.external_embedding_filter)
#
#	    if options.external_embedding_filter_new:
#		W2Vnew = w2vread.ReadW2V(options.external_embedding, 
#				      binary=not options.external_embedding_Textual, 
#				      filterfile=options.external_embedding_filter_new)

            filterfiles = []
            if options.external_embedding_filter:
                filterfiles.append(options.external_embedding_filter)
                if options.external_embedding_filter_new:
                    filterfiles.append(options.external_embedding_filter_new)
	    W2V = w2vread2.ReadW2V(options.external_embedding, 
				  binary=not options.external_embedding_Textual, 
				  filterfiles=filterfiles)

				
	    self.external_embedding = W2V.embeddings[0]

	    # number of dimension of the embeddings
            self.edim = len(self.external_embedding.values()[0])
	   
            self.noextrn = [0.0 for _ in xrange(self.edim)]

	    # we create a dico word:index
            self.extrnd = {word: i + 3 for i, word in enumerate(self.external_embedding)}

	    if options.external_embedding_filter_new:
		# adding words embeddigns for words not yet seen during training	
		#for word in W2Vnew.embeddings.keys():
		#	if not self.external_embedding.has_key(word):
		#		self.extrnd[word] = len(self.extrnd) + 3
		#		self.external_embedding[word] = W2Vnew.embeddings[word]

		for word in W2V.embeddings[1].keys():
			if not self.external_embedding.has_key(word):
				self.extrnd[word] = len(self.extrnd) + 3
				self.external_embedding[word] = W2V.embeddings[1][word]

	   
	    # ininitialise the size of the embeddings
            self.model.add_lookup_parameters("extrn-lookup", (len(self.external_embedding) + 3, self.edim))
	  

            for word, i in self.extrnd.iteritems():
		#print "\nAVANT", word, i, lookup(self.model["extrn-lookup"], i).value()[:4]
	        #print "w2v  ", i, word, self.external_embedding[word][:4]
                self.model["extrn-lookup"].init_row(i, self.external_embedding[word])
		#print "APRES", word, i, lookup(self.model["extrn-lookup"], i).value()[:4]
            self.extrnd['*PAD*'] = 1
            self.extrnd['*INITIAL*'] = 2

            print 'Loaded external embeddings. Vector of %d dimensions' % self.edim

	# 3*rdims (GENDER, NUMBER, PERSON)
        dims = self.wdims + self.pdims + 3*self.rdims + (self.edim if self.external_embedding is not None else 0)
        self.blstmFlag = options.blstmFlag
        self.bibiFlag = options.bibiFlag

        if self.bibiFlag:
            self.surfaceBuilders = [LSTMBuilder(1, dims, self.ldims * 0.5, self.model),
                                    LSTMBuilder(1, dims, self.ldims * 0.5, self.model)]
            self.bsurfaceBuilders = [LSTMBuilder(1, self.ldims, self.ldims * 0.5, self.model),
                                     LSTMBuilder(1, self.ldims, self.ldims * 0.5, self.model)]
        elif self.blstmFlag:
            if self.layers > 0:
                self.surfaceBuilders = [LSTMBuilder(self.layers, dims, self.ldims * 0.5, self.model), LSTMBuilder(self.layers, dims, self.ldims * 0.5, self.model)]
            else:
                self.surfaceBuilders = [SimpleRNNBuilder(1, dims, self.ldims * 0.5, self.model), LSTMBuilder(1, dims, self.ldims * 0.5, self.model)]

        self.hidden_units = options.hidden_units
        self.hidden2_units = options.hidden2_units
        self.vocab['*PAD*'] = 1
        self.pos['*PAD*'] = 1
        #self.cpos['*PAD*'] = 1
        self.GENDER['*PAD*'] = 1
        self.NUMBER['*PAD*'] = 1
        self.PERSON['*PAD*'] = 1

        self.vocab['*INITIAL*'] = 2
        self.pos['*INITIAL*'] = 2
        #self.cpos['*INITIAL*'] = 2
	self.GENDER['*INITIAL*'] = 2
	self.NUMBER['*INITIAL*'] = 2
	self.PERSON['*INITIAL*'] = 2

        self.model.add_lookup_parameters("word-lookup", (len(words) + 3, self.wdims))
        self.model.add_lookup_parameters("pos-lookup", (len(pos) + 3, self.pdims))
	#self.model.add_lookup_parameters("cpos-lookup", (len(cpos) + 3, self.rdims))
	self.model.add_lookup_parameters("GENDER-lookup", (len(GENDER) + 3, self.rdims))
	self.model.add_lookup_parameters("NUMBER-lookup", (len(NUMBER) + 3, self.rdims))
	self.model.add_lookup_parameters("PERSON-lookup", (len(PERSON) + 3, self.rdims))
        self.model.add_lookup_parameters("rels-lookup", (len(rels), self.rdims))

        self.model.add_parameters("word-to-lstm", (self.ldims, self.wdims + self.pdims + (self.edim if self.external_embedding is not None else 0)))
        self.model.add_parameters("word-to-lstm-bias", (self.ldims))
        self.model.add_parameters("lstm-to-lstm", (self.ldims, self.ldims * self.nnvecs + self.rdims))
        self.model.add_parameters("lstm-to-lstm-bias", (self.ldims))

        self.model.add_parameters("hidden-layer", (self.hidden_units, self.ldims * self.nnvecs * (self.k + 1)))
        self.model.add_parameters("hidden-bias", (self.hidden_units))

        self.model.add_parameters("hidden2-layer", (self.hidden2_units, self.hidden_units))
        self.model.add_parameters("hidden2-bias", (self.hidden2_units))

        self.model.add_parameters("output-layer", (3, self.hidden2_units if self.hidden2_units > 0 else self.hidden_units))
        self.model.add_parameters("output-bias", (3))

        self.model.add_parameters("rhidden-layer", (self.hidden_units, self.ldims * self.nnvecs * (self.k + 1)))
        self.model.add_parameters("rhidden-bias", (self.hidden_units))

        self.model.add_parameters("rhidden2-layer", (self.hidden2_units, self.hidden_units))
        self.model.add_parameters("rhidden2-bias", (self.hidden2_units))

        self.model.add_parameters("routput-layer", (2 * (len(self.irels) + 0) + 1, self.hidden2_units if self.hidden2_units > 0 else self.hidden_units))
        self.model.add_parameters("routput-bias", (2 * (len(self.irels) + 0) + 1))


    def __evaluate(self, stack, buf, train):
        topStack = [ stack.roots[-i-1].lstms if len(stack) > i else [self.empty] for i in xrange(self.k) ]
        topBuffer = [ buf.roots[i].lstms if len(buf) > i else [self.empty] for i in xrange(1) ]

        input = concatenate(list(chain(*(topStack + topBuffer))))

        if self.hidden2_units > 0:
            routput = (self.routLayer * self.activation(self.rhid2Bias + self.rhid2Layer * self.activation(self.rhidLayer * input + self.rhidBias)) + self.routBias)
        else:
            routput = (self.routLayer * self.activation(self.rhidLayer * input + self.rhidBias) + self.routBias)

        if self.hidden2_units > 0:
            output = (self.outLayer * self.activation(self.hid2Bias + self.hid2Layer * self.activation(self.hidLayer * input + self.hidBias)) + self.outBias)
        else:
            output = (self.outLayer * self.activation(self.hidLayer * input + self.hidBias) + self.outBias)

        scrs, uscrs = routput.value(), output.value()

        uscrs0 = uscrs[0]
        uscrs1 = uscrs[1]
        uscrs2 = uscrs[2]
        if train:
            output0 = output[0]
            output1 = output[1]
            output2 = output[2]
            ret = [ [ (rel, 0, scrs[1 + j * 2] + uscrs1, routput[1 + j * 2 ] + output1) for j, rel in enumerate(self.irels) ] if len(stack) > 0 and len(buf) > 0 else [],  
                    [ (rel, 1, scrs[2 + j * 2] + uscrs2, routput[2 + j * 2 ] + output2) for j, rel in enumerate(self.irels) ] if len(stack) > 1 else [],  
                    [ (None, 2, scrs[0] + uscrs0, routput[0] + output0) ] if len(buf) > 0 else [] ]
        else:
            s1,r1 = max(zip(scrs[1::2],self.irels))
            s2,r2 = max(zip(scrs[2::2],self.irels))
            s1 += uscrs1
            s2 += uscrs2
            ret = [ [ (r1, 0, s1) ] if len(stack) > 0 and len(buf) > 0 else [],  
                    [ (r2, 1, s2) ] if len(stack) > 1 else [],  
                    [ (None, 2, scrs[0] + uscrs0) ] if len(buf) > 0 else [] ]
        return ret
        #return [ [ (rel, 0, scrs[1 + j * 2 + 0] + uscrs[1], routput[1 + j * 2 + 0] + output[1]) for j, rel in enumerate(self.irels) ] if len(stack) > 0 and len(buf) > 0 else [],  
        #         [ (rel, 1, scrs[1 + j * 2 + 1] + uscrs[2], routput[1 + j * 2 + 1] + output[2]) for j, rel in enumerate(self.irels) ] if len(stack) > 1 else [],  
        #         [ (None, 2, scrs[0] + uscrs[0], routput[0] + output[0]) ] if len(buf) > 0 else [] ]


    def Save(self, filename):
        self.model.save(filename)


    def Load(self, filename):
        self.model.load(filename)

    def Init(self):
        self.word2lstm = parameter(self.model["word-to-lstm"])
        self.lstm2lstm = parameter(self.model["lstm-to-lstm"])

        self.word2lstmbias = parameter(self.model["word-to-lstm-bias"])
        self.lstm2lstmbias = parameter(self.model["lstm-to-lstm-bias"])

        self.hid2Layer = parameter(self.model["hidden2-layer"])
        self.hidLayer = parameter(self.model["hidden-layer"])
        self.outLayer = parameter(self.model["output-layer"])

        self.hid2Bias = parameter(self.model["hidden2-bias"])
        self.hidBias = parameter(self.model["hidden-bias"])
        self.outBias = parameter(self.model["output-bias"])

        self.rhid2Layer = parameter(self.model["rhidden2-layer"])
        self.rhidLayer = parameter(self.model["rhidden-layer"])
        self.routLayer = parameter(self.model["routput-layer"])

        self.rhid2Bias = parameter(self.model["rhidden2-bias"])
        self.rhidBias = parameter(self.model["rhidden-bias"])
        self.routBias = parameter(self.model["routput-bias"])

        evec = lookup(self.model["extrn-lookup"], 1) if self.external_embedding is not None else None
        paddingWordVec = lookup(self.model["word-lookup"], 1)
        paddingPosVec = lookup(self.model["pos-lookup"], 1) if self.pdims > 0 else None
        #paddingCPosVec = lookup(self.model["cpos-lookup"], 1) if self.rdims > 0 else None
	paddingGENDERVec = lookup(self.model["GENDER-lookup"], 1) if self.rdims > 0 else None
	paddingNUMBERVec = lookup(self.model["NUMBER-lookup"], 1) if self.rdims > 0 else None
	paddingPERSONVec = lookup(self.model["PERSON-lookup"], 1) if self.rdims > 0 else None



        paddingVec = tanh(self.word2lstm * concatenate(filter(None, [paddingWordVec, paddingPosVec, evec])) + self.word2lstmbias )
        self.empty = paddingVec if self.nnvecs == 1 else concatenate([paddingVec for _ in xrange(self.nnvecs)])


    def getWordEmbeddings(self, sentence, train):
        for root in sentence:
            c = float(self.wordsCount.get(root.norm, 0))
            dropFlag =  not train or (random.random() < (c/(0.25+c)))
            root.wordvec = lookup(self.model["word-lookup"], int(self.vocab.get(root.norm, 0)) if dropFlag else 0)


	    #root.cposvec = lookup(self.model["cpos-lookup"], int(self.cpos[root.cpos])) if self.cdims > 0 else None
	    root.GENDERvec = lookup(self.model["GENDER-lookup"], int(self.GENDER[root.GENDER])) if self.rdims > 0 else None
	    root.NUMBERvec = lookup(self.model["NUMBER-lookup"], int(self.NUMBER[root.NUMBER])) if self.rdims > 0 else None
	    root.PERSONvec = lookup(self.model["PERSON-lookup"], int(self.PERSON[root.PERSON])) if self.rdims > 0 else None

	    #if not train: print "ee", root.GENDERvec.value()

	    if train:
                root.posvec = lookup(self.model["pos-lookup"], int(self.pos[root.pos])) if self.pdims > 0 else None
	    else:
		try:
	            root.posvec = lookup(self.model["pos-lookup"], int(self.pos[root.pos])) if self.pdims > 0 else None
	   	except:
		    try:
		    	root.posvec = lookup(self.model["pos-lookup"], int(self.pos[root.pos[:-1]])) if self.pdims > 0 else None
		    except:
			pos = root.pos.split("-")[0]
			ok = False
			for p in self.pos:
			    if p.startswith(p):
				root.posvec = lookup(self.model["pos-lookup"], int(self.pos[p])) if self.pdims > 0 else None
				ok = True
				break
			if not ok:
			    root.posvec = lookup(self.model["pos-lookup"], int(self.pos["GN-NC"])) if self.pdims > 0 else None
		    	

            if self.external_embedding is not None:
                if not dropFlag and random.random() < 0.5:
                    root.evec = lookup(self.model["extrn-lookup"], 0)
                elif root.form in self.external_embedding:
                    root.evec = lookup(self.model["extrn-lookup"], self.extrnd[root.form], update = True)
                elif root.norm in self.external_embedding:
                    root.evec = lookup(self.model["extrn-lookup"], self.extrnd[root.norm], update = True)
                else:
                    root.evec = lookup(self.model["extrn-lookup"], 0)
            else:
                root.evec = None
	    #print "ROOT ", root.form
	    #print "  VEC", root.wordvec.value()
            #root.ivec = concatenate(filter(None, [root.wordvec, root.posvec, root.evec]))
            root.ivec = concatenate(filter(None, [root.wordvec, root.posvec, #root.cposvec,
						  root.GENDERvec, root.NUMBERvec, root.PERSONvec,
						  root.evec]))



        if self.blstmFlag:
            forward  = self.surfaceBuilders[0].initial_state()
            backward = self.surfaceBuilders[1].initial_state()

            for froot, rroot in zip(sentence, reversed(sentence)):
                forward = forward.add_input( froot.ivec )
                backward = backward.add_input( rroot.ivec )
                froot.fvec = forward.output()
                rroot.bvec = backward.output()
            for root in sentence:
                root.vec = concatenate( [root.fvec, root.bvec] )

            if self.bibiFlag:
                bforward  = self.bsurfaceBuilders[0].initial_state()
                bbackward = self.bsurfaceBuilders[1].initial_state()

                for froot, rroot in zip(sentence, reversed(sentence)):
                    bforward = bforward.add_input( froot.vec )
                    bbackward = bbackward.add_input( rroot.vec )
                    froot.bfvec = bforward.output()
                    rroot.bbvec = bbackward.output()
                for root in sentence:
                    root.vec = concatenate( [root.bfvec, root.bbvec] )

        else:
            for root in sentence:
                root.ivec = (self.word2lstm * root.ivec) + self.word2lstmbias
                root.vec = tanh( root.ivec )


    def Predict(self, conll_path, is_string=False):
	conllFP = None
	#OLD=False
	#self.use_root=False
	if is_string:
		conllFP = StringIO.StringIO(conll_path)
	else:
		conllFP = open(conll_path, 'r')
        #with open(conll_path, 'r') as conllFP:
	
	if conllFP:
            for iSentence, sentence in enumerate(read_conll(conllFP, False)):
                self.Init()
		
		if self.use_root:
			# garder le noeud "*root*" (peut causer plusieurs racines)
                	sentence = sentence[1:] + [sentence[0]]
		else:
			sentence = sentence[1:]
		#print "aaaa ", sentence[0], type(sentence)
                self.getWordEmbeddings(sentence, False)
                stack = ParseForest([])
                buf = ParseForest(sentence)

                for root in sentence:
                    root.lstms = [root.vec for _ in xrange(self.nnvecs)]

                hoffset = 1 if self.headFlag else 0

		cttrans = 0
		#print "\n====="
                while len(buf) > 0 or len(stack) > 1 :
                    scores = self.__evaluate(stack, buf, False)
                    best = max(chain(*scores), key = itemgetter(2) )

		    #print "\nBUFFER: ", buf
		    #print "STACK:  ", stack
		    #print scores

		    cttrans += 1
		    # transitions
                    if best[1] == 2:
			# SHIFT
                        stack.roots.append(buf.roots[0])
                        del buf.roots[0]
			#print cttrans, "SHIFT"

                    elif best[1] == 0:
			# LEFT (?) ARC
			#print cttrans, "LEFT"
                        child = stack.roots.pop()
                        parent = buf.roots[0]
			
                        child.pred_parent_id = parent.id
                        child.pred_relation = best[0]

			#print child, child.form, child.pred_parent_id 

                        bestOp = 0
                        if self.rlMostFlag:
                            parent.lstms[bestOp + hoffset] = child.lstms[bestOp + hoffset]
                        if self.rlFlag:
                            parent.lstms[bestOp + hoffset] = child.vec

                    elif best[1] == 1:
			# RIGHT ARC
			#print cttrans, "RIGHT"
                        child = stack.roots.pop()
                        parent = stack.roots[-1]

                        child.pred_parent_id = parent.id
                        child.pred_relation = best[0]

                        bestOp = 1
                        if self.rlMostFlag:
                            parent.lstms[bestOp + hoffset] = child.lstms[bestOp + hoffset]
                        if self.rlFlag:
                            parent.lstms[bestOp + hoffset] = child.vec

                renew_cg()
		if self.use_root:
                	yield [sentence[-1]] + sentence[:-1]
		else:
			# write_conll coupe le premier mot, il faut mettre qq chose ici
			yield [sentence[-1]] + sentence


    def Train(self, conll_path, epoch):
        mloss = 0.0
        errors = 0
        batch = 0
        eloss = 0.0
        eerrors = 0
        lerrors = 0
        etotal = 0
        ltotal = 0
        ninf = -float('inf')

        hoffset = 1 if self.headFlag else 0

        start1 = start = time.time()
	onlyNonProjectives = True
        with open(conll_path, 'r') as conllFP:
            shuffledData = list(read_conll(conllFP, onlyNonProjectives))
            random.shuffle(shuffledData)

            errs = []
            eeloss = 0.0

            self.Init()

	    numOfSent = len(shuffledData)
	    displayFreq = 500
	    if numOfSent < 2000: displayFreq = 200
            for iSentence, sentence in enumerate(shuffledData):
                if iSentence % displayFreq == 0 and iSentence != 0:
                    #print 'Processing sentence number:', iSentence, 'Loss:', eloss / etotal, 'Errors:', (float(eerrors)) / etotal, 'Labeled Errors:', (float(lerrors) / etotal) , 'Time', time.time()-start
		    timeSpent = time.time()-start
		    totalTimeSpent = time.time()-start1
		    timeToGo = totalTimeSpent*(numOfSent-iSentence) / iSentence
		    print 'Epoch: %2d sentence number: %6d/%d Loss: %.5f Errors: %.5f Labeled Errors: %.5f Time: %.1f s, total: %.1f s ETA: %.1f s' \
			% (epoch+1,
			   iSentence,
                           numOfSent,
			   (eloss / etotal),
			   (float(eerrors) / etotal),
			   (float(lerrors) / etotal),
			   timeSpent, totalTimeSpent,
			   timeToGo
			  )
                    start = time.time()
                    eerrors = 0
                    eloss = 0.0
                    etotal = 0
                    lerrors = 0
                    ltotal = 0
              
		
		if self.use_root:
			# garder le noeud "*root*" rajoute par read_conll (peut causer plusieurs racines)
                	sentence = sentence[1:] + [sentence[0]]
		else:
			sentence = sentence[1:]

                self.getWordEmbeddings(sentence, True)
                stack = ParseForest([])
                buf = ParseForest(sentence)

                for root in sentence:
                    root.lstms = [root.vec for _ in xrange(self.nnvecs)]

                hoffset = 1 if self.headFlag else 0

                while len(buf) > 0 or len(stack) > 1 :
                    scores = self.__evaluate(stack, buf, True)
                    scores.append([(None, 3, ninf ,None)])

                    alpha = stack.roots[:-2] if len(stack) > 2 else []
                    s1 = [stack.roots[-2]] if len(stack) > 1 else []
                    s0 = [stack.roots[-1]] if len(stack) > 0 else []
                    b = [buf.roots[0]] if len(buf) > 0 else []
                    beta = buf.roots[1:] if len(buf) > 1 else []

                    left_cost  = ( len([h for h in s1 + beta if h.id == s0[0].parent_id]) + 
                                   len([d for d in b + beta if d.parent_id == s0[0].id]) )  if len(scores[0]) > 0 else 1

                    right_cost = ( len([h for h in b + beta if h.id == s0[0].parent_id]) +
                                   len([d for d in b + beta if d.parent_id == s0[0].id]) )  if len(scores[1]) > 0 else 1

                    shift_cost = ( len([h for h in s1 + alpha if h.id == b[0].parent_id]) +
                                   len([d for d in s0 + s1 + alpha if d.parent_id == b[0].id]) )  if len(scores[2]) > 0 else 1

                    costs = (left_cost, right_cost, shift_cost, 1)
		    bestOK = True
		    try:
	            	bestValid = max(( s for s in chain(*scores) if costs[s[1]] == 0 and ( s[1] == 2 or  s[0] == stack.roots[-1].relation ) ), key=itemgetter(2))
#			print "best",bestValid
		    except:
			bestOK = False


		    try:
			bestWrong = max(( s for s in chain(*scores) if costs[s[1]] != 0 or  ( s[1] != 2 and s[0] != stack.roots[-1].relation ) ), key=itemgetter(2))
		    except:
			print "wrong", bestWrong
			bestOK = False


		    # bestValid or bastWrong may fail when chain(*scores) gives an empty list
		    # in this (rare) case we keep the last best
		    # Will crash if the first word has an empty list
		    if bestOK:
			best = bestValid if ( (not self.oracle) or (bestValid[2] - bestWrong[2] > 1.0) or (bestValid[2] > bestWrong[2] and random.random() > 0.1) ) else bestWrong

		 
                    if best[1] == 2:
			# we learned a SHIFT
                        stack.roots.append(buf.roots[0])
                        del buf.roots[0]

                    elif best[1] == 0:
			# we learnded a LEFT ARC
                        child = stack.roots.pop()
                        parent = buf.roots[0]

                        child.pred_parent_id = parent.id
                        child.pred_relation = best[0]

                        bestOp = 0
                        if self.rlMostFlag:
                            parent.lstms[bestOp + hoffset] = child.lstms[bestOp + hoffset]
                        if self.rlFlag:
                            parent.lstms[bestOp + hoffset] = child.vec

                    elif best[1] == 1:
			# RIGHT ARC
                        child = stack.roots.pop()
                        parent = stack.roots[-1]

                        child.pred_parent_id = parent.id
                        child.pred_relation = best[0]

                        bestOp = 1
                        if self.rlMostFlag:
                            parent.lstms[bestOp + hoffset] = child.lstms[bestOp + hoffset]
                        if self.rlFlag:
                            parent.lstms[bestOp + hoffset] = child.vec

                    if bestValid[2] < bestWrong[2] + 1.0:
                        loss = bestWrong[3] - bestValid[3]
                        mloss += 1.0 + bestWrong[2] - bestValid[2]
                        eloss += 1.0 + bestWrong[2] - bestValid[2]
                        errs.append(loss)

                    if best[1] != 2 and (child.pred_parent_id != child.parent_id or child.pred_relation != child.relation):
                        lerrors += 1
                        if child.pred_parent_id != child.parent_id:
                            errors += 1
                            eerrors += 1

                    etotal += 1

                if len(errs) > 50: # or True:
		    #print "too many errors"
                    #eerrs = ((esum(errs)) * (1.0/(float(len(errs)))))
                    eerrs = esum(errs)
                    scalar_loss = eerrs.scalar_value()
                    eerrs.backward()
                    self.trainer.update()
                    errs = []
                    lerrs = []

                    renew_cg()
                    self.Init()

        if len(errs) > 0:
            eerrs = (esum(errs)) # * (1.0/(float(len(errs))))
            eerrs.scalar_value()
            eerrs.backward()
            self.trainer.update()

            errs = []
            lerrs = []

            renew_cg()

        self.trainer.update_epoch()
        print "Loss: %.4f time spent in epoch %.1f min" % (mloss/iSentence, (time.time()-start1)/60)

