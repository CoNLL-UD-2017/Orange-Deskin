
import math
import struct
import string
import sys
import re


class ReadW2V:
    def __init__(self, w2vbin_filename, binary=True, filterfiles=[]):
	#fn = "lemmas.300-dim.10-win.cbow.bin"
	#fn = "posCpos.50-dim.10-win.cbow.bin"

	self.keep = []
        for filterfile in filterfiles:
            keep = set()
	    print "W2V: loading word list %s of embeddings to keep" % filterfile
	    #self.keep = set()
	    ifp = open(filterfile)
	    for line in ifp.readlines():
		line = line.strip()
		keep.add(line)
	    ifp.close()
	    print "W2V: %d words to keep" % len(keep)
            self.keep.append(keep)
            

	if binary:
	    print "W2V: loading binary w2v file", w2vbin_filename
	    fp = open(w2vbin_filename, 'rb')
	else:
	    print "W2V: loading textual w2v file", w2vbin_filename
	    fp = open(w2vbin_filename, 'r')

	# read first line to get nunmber of dimensions
	line = fp.readline()
	elems = line.strip().split()

	self.words = int(elems[0])
	self.dims = int(elems[1])
        # dico for vectors (or vectors chosen with first filterfile)
	self.embeddings = [{}]
        for x in range(len(filterfiles) -1):
            # dicos for vectors chosen by all other filterfiles
            self.embeddings.append({})
        
	
	print "W2V: %d dimensions" % self.dims

	self.filter = re.compile("[0-9,\.;:\(\)&\?!%#$@]")

	if binary:
	    self.readbin(fp)
#	else:
#	    self.readtext(fp)

#    def readtext(self, fp):
#	line = fp.readline()
#	ct = 0
#	filtered = 0
#	while line:
#	    ct += 1
#	    elems = line.strip().split(" ")
#	    word = elems[0]
#	    if self.filter.search(word):
#		filtered += 1
#	    else:
#		if self.keep and word in self.keep:
#		    vector = []
#		    #print elems
#	            for floattext in elems[1:]:
#			#print "eee", floattext
#			vector.append(float(floattext))
#	            self.embeddings[word] = self.normalise(vector)
#	    if ct % 10000 == 0:
#		sys.stderr.write("%d vectors read (%d ignored)...\n" % (ct,filtered))
#	    line = fp.readline()
#	sys.stderr.write("All %d vectors read (%d ignored)\n" % (ct,filtered))

    def readbin(self, fp):
	mot = []
	ct = 0
	eof_found = False
	while True:
	    while True:
		# read word until the first blank
		buffer = fp.read(1)
		if len(buffer) != 1:
		    # found end of file (less words than expected due to output filter of word2vec
		    #print "B",buffer
		    #print "W",word
		    eof_found = True
		    break
		tuple = struct.unpack("c", buffer)
		if tuple[0] != ' ': 
			mot.append(tuple[0])
		else:
			break
	    if eof_found:
		break
	    #print string.join(mot, "")
	    word = string.join(mot, "")
	    #print "WORD:", mot
	    mot = []
	    ct += 1
	    if ct % 50000 == 0:
                messages = []
                for e in self.embeddings:
                    messages.append("%s" % len(e))
		sys.stdout.write("W2V: %d word vectors read (%s kept)\n" % (ct, string.join(messages, "/")))
		sys.stdout.flush()
	    # read self.dims floats: the vector
	    f = struct.unpack('f'*self.dims, fp.read(self.dims*4))
	    # read the final LF
	    fp.read(1)
	    #print "VECTOR: ", list(f)
	    #print "  norm: ", self.normalise(f)
            if not self.keep:
                # we load all vectors
                self.embeddings[0][word] = self.normalise(f)
            else:
                keepct = 0
                for keep in self.keep:
                    if word in keep:
                        self.embeddings[keepct][word] = self.normalise(f)
                        break
                    keepct += 1

	    if ct == self.words:
		break

	fp.close()
        for e in self.embeddings:
            print "W2V: %d word vectors loaded" % len(e)

    def normalise(self, fvec):
	res = 0.0
	for v in fvec:
		res += (v*v)
	length = math.sqrt(res)

	fvecres = []
	for v in fvec:
		fvecres.append(v/length)
	return fvecres


if __name__ == "__main__":
    import sys

    binary = True
    if len(sys.argv) > 2:
	binary = False
    r = ReadW2V(sys.argv[1], binary)

    ct = 0
	
    while True:
	w = raw_input("word> ")
	print "<%s>" % w
	if r.embeddings.has_key(w):
	   print r.embeddings[w]
	

