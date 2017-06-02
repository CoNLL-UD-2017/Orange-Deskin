from collections import Counter
import re
import os

class ConllEntry:
    def __init__(self, id, form, pos, cpos, features, parent_id=None, relation=None):
        self.id = id
        self.form = form
        self.norm = normalize(form)
        self.cpos = cpos.upper()
	self.features = {} # name: value
	self.NUMBER = "_"
	self.PERSON = "_"
	self.GENDER = "_"
	if features and features != "_":
		fs = features.split("|")
		for f in fs:
			nv = f.split("=")
			if nv == 2:
				#self.features[nv[0]] = nv[1]
				if nv[0] == "g" or nv[0] == "GENRE": # features from FTB or Tilt 
					self.GENDER = nv[1]
				elif nv[0] == "p" or nv[0] == "PERSONNE": # features from FTB or Tilt 
					self.GENDER = nv[1]
				elif nv[0] == "n" or nv[0] == "NUMBER": # features from FTB or Tilt 
					self.GENDER = nv[1]
				
	
        self.pos = pos.upper()
	if self.pos == "_":
	    self.pos = self.cpos
        self.parent_id = parent_id
        self.relation = relation

    def __repr__(self):
	try:
	    return "%s:%s:%s:%s:%s" % (self.id, self.form, self.cpos, self.pred_parent_id, self.pred_relation)
	except:
	    return "%s:%s:%s:?:?" % (self.id, self.form, self.cpos)

import string

class ParseForest:
    def __init__(self, sentence):
        self.roots = list(sentence)

        for root in self.roots:
            #root.children = []
            root.scores = None
            root.parent = None
            root.pred_parent_id = 0 # None
            root.pred_relation = 'root' # 'rroot' # None
            root.vecs = None
            root.lstms = None

    def __len__(self):
        return len(self.roots)

    def __repr__(self):
	res = []
	for x in self.roots:
		form = x.form
		#form = repr(x)
		#if x.pred_relation != "rroot":
		#form += "(%s:%s)" % (x.pred_relation, x.pred_parent_id)
		res.append(form)
	return string.join(res, ", ")


    def Attach(self, parent_index, child_index):
        parent = self.roots[parent_index]
        child = self.roots[child_index]

        child.pred_parent_id = parent.id
        del self.roots[child_index]


def isProj(sentence):
    forest = ParseForest(sentence)
    unassigned = {entry.id: sum([1 for pentry in sentence if pentry.parent_id == entry.id]) for entry in sentence}

    for _ in xrange(len(sentence)):
        for i in xrange(len(forest.roots) - 1):
            if forest.roots[i].parent_id == forest.roots[i+1].id and unassigned[forest.roots[i].id] == 0:
                unassigned[forest.roots[i+1].id]-=1
                forest.Attach(i+1, i)
                break
            if forest.roots[i+1].parent_id == forest.roots[i].id and unassigned[forest.roots[i+1].id] == 0:
                unassigned[forest.roots[i].id]-=1
                forest.Attach(i, i+1)
                break

    return len(forest.roots) == 1

def vocab(conll_path, WITHCPOS=False):
    wordsCount = Counter()
    posCount = Counter()
    cposCount = Counter()
    relCount = Counter()

    GENDERCount = Counter()
    NUMBERCount = Counter()
    PERSCount = Counter()

    onlyNonProjectives = True
    with open(conll_path, 'r') as conllFP:
        for sentence in read_conll(conllFP, onlyNonProjectives):
            wordsCount.update([node.norm for node in sentence])
            posCount.update([node.pos for node in sentence])
            cposCount.update([node.cpos for node in sentence])
            relCount.update([node.relation for node in sentence])
	    if WITHCPOS:	
		GENDERCount.update([node.GENDER for node in sentence])
		NUMBERCount.update([node.NUMBER for node in sentence])
		PERSCount.update([node.PERSON for node in sentence])

    if WITHCPOS:
	return (wordsCount, {w: i for i, w in enumerate(wordsCount.keys())},
					posCount.keys(),
					cposCount.keys(), 
					GENDERCount.keys(), 
					NUMBERCount.keys(), 
					PERSCount.keys(), 
					relCount.keys())
    else:
    	return (wordsCount, {w: i for i, w in enumerate(wordsCount.keys())},  posCount.keys(), relCount.keys())


def read_conll(fh, proj):
    dropped = 0
    read = 0
    root = ConllEntry(0, '*root*', 'ROOT-POS', 'ROOT-CPOS', "_", 0, 'rroot')
    tokens = [root]
    for line in fh:
        tok = line.strip().split("\t")
	#print "\n", line
	#print tok
        if not tok or len(tok) < 2:
            if len(tokens)>1:
                if not proj or isProj(tokens):
                    yield tokens
                else:
                    #print 'Non-projective sentence dropped'
                    dropped += 1
                read += 1
            tokens = [root]
            id = 0
        else:
            #tokens.append(ConllEntry(int(tok[0]), tok[1], tok[4], tok[3], int(tok[6]) if tok[6] != '_' else -1, tok[7]))
	    tokens.append(ConllEntry(int(tok[0]), tok[1], tok[4], tok[3], tok[5], int(tok[6]) if tok[6] != '_' else -1, tok[7]))
    if len(tokens) > 1:
        yield tokens

    if (dropped): print dropped, 'dropped non-projective sentences.'
    if (read): print read, 'sentences read.'


def write_conll(fn, conll_gen):
    with open(fn, 'w') as fh:
        for sentence in conll_gen:
            for entry in sentence[1:]:
                fh.write('\t'.join([str(entry.id), entry.form, '_', entry.cpos, entry.pos, '_', str(entry.pred_parent_id), entry.pred_relation, '_', '_']))
                fh.write('\n')
            fh.write('\n')
    fh.close()


evalscript="~/bin/toolbin/conll/evaluation_script/conll17_ud_eval.py"
weightfile="~/bin/toolbin/conll/evaluation_script/weights.clas"

# runs eval script and returns weighted LAS
def runeval(infile, outfile, verbose=True):
    print "predicting %s" % infile
    command = "%s --weights %s %s %s > %s.txt4" % (evalscript, weightfile, infile, outfile, outfile)
    #+ options.conll_dev + "  " + devpath  + " > " + devpath + '.txt4'
    print "executing: %s" % command
    os.system(command)
    # just show current LAS
    ifp = open(outfile + '.txt4')
    weightedLAS = 0
    for line in ifp.readlines():
	line = line.strip()
	if line.startswith("Weigh"):
		elems = line.split("|")
		weightedLAS = float(elems[3])
	if verbose: print line
    ifp.close()
    return weightedLAS


numberRegex = re.compile("[0-9]+|[0-9]+\\.[0-9]+|[0-9]+[0-9,]+");
def normalize(word):
    return 'NUM' if numberRegex.match(word) else word.lower()

cposTable = {"PRP$": "PRON", "VBG": "VERB", "VBD": "VERB", "VBN": "VERB", ",": ".", "''": ".", "VBP": "VERB", "WDT": "DET", "JJ": "ADJ", "WP": "PRON", "VBZ": "VERB", 
             "DT": "DET", "#": ".", "RP": "PRT", "$": ".", "NN": "NOUN", ")": ".", "(": ".", "FW": "X", "POS": "PRT", ".": ".", "TO": "PRT", "PRP": "PRON", "RB": "ADV", 
             ":": ".", "NNS": "NOUN", "NNP": "NOUN", "``": ".", "WRB": "ADV", "CC": "CONJ", "LS": "X", "PDT": "DET", "RBS": "ADV", "RBR": "ADV", "CD": "NUM", "EX": "DET", 
             "IN": "ADP", "WP$": "PRON", "MD": "VERB", "NNPS": "NOUN", "JJS": "ADJ", "JJR": "ADJ", "SYM": "X", "VB": "VERB", "UH": "X", "ROOT-POS": "ROOT-CPOS", 
             "-LRB-": ".", "-RRB-": "."}
