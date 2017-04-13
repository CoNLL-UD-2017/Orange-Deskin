#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-

# une classe pour lire des documents CONLL (en UTF8)

import sys, string, codecs
import string
import StringIO
import re

#sys.stdout = codecs.getwriter('utf8')(sys.stdout)
#sys.stderr = codecs.getwriter('utf8')(sys.stderr)

sys.stdout = codecs.getwriter('utf-8')(sys.stdout)


#def xmlify(val):
#    val = val.replace('&', '&amp;')
#    val = val.replace('"', '&quot;')
#    val = val.replace('<', '&lt;')
#    val = val.replace('>', '&gt;')
#    return val


cats = { "GV-[RP].*": "VERB",
         "GN-A.*" : "ADJ",
         "TIR" : "PUNCT",
         "GV-[EACM].*": "AUX",
         "GN-I?D.*" : "DET",
         "PP-ATTR" : "DET",
         "PI" : "DET",
         "PD-.*" : "DET",
         "GN-PART-AMB" : "ADP",
         "GP-G" : "ADP",
         "GP-EN" : "ADP",
         "PP-Y" : "PRON",
         "VIDE-L" : "PRON",
         "GN-NP.*" : "PROPN",
         "GN-N.*" : "NOUN",
         "XXX" : "NOUN",
         "GP-S.*" : "ADP",
         "COORD" : "CONJ",
         "PRN-S" : "PRON",
         "NBR" : "NUM",
         "PQ.*" : "PRON",
         "PR.*" : "PRON",
         "PX.*" : "PRON",
         "CS" : "SCONJ",
         "SEPF" : "PUNCT",
         "VIRGULE" : "PUNCT",
         "R.*" : "ADV",
         "GN-MES" : "ADV",
         "DATE" : "NOUN",
         "GN-TITRE" : "NOUN",
         "GP-N" : "ADP",
         "PP-[OI].*" : "PRON",
         "GN-YEAR": "NUM",
    }

catRE = {}
for k,v in cats.items():
    catRE[re.compile("^%s$"% k)] = v


def sortWord(a, b):
    return cmp(a.ident, b.ident)

def sortFreq(a, b):
    return cmp(b[1], a[1])


def normaliseIDs(words):
    # pas nécessaire de trier, non ? les lignes devraient être dans le bon ordre
    #words.sort(sortWord)
    # a appell
    newident = 1
    oldnewidents = {0:0} # oldid: newid
    for w in words:
        #print "ttttt", w.ident, w.form, w.head
        oldnewidents[w.ident] = newident
        newident += 1
    iitems = oldnewidents.items()
    iitems.sort()
    #print "ooooo", iitems
    for w in words:
        w.ident = oldnewidents.get(w.ident)
        if w.head != 0 and w.head < 10000:
            w.head = oldnewidents.get(w.head)
        #print "uuuuu", w.ident, w.form, w.head

def decifyIds(words):
    # multiplier tous les indexes par 10 pour pouvoir insérer un nouveau mot
    for w in words:
        w.ident = w.ident * 10 
        w.head = w.head * 10
    
# classes utilisées pour parser des fichiers CONLL
class Word:
    # un mot d'un fichier CONLL (ligne)
    def __init__(self, line, shift=0):
        self.error = ""
        if isinstance(line, Word):
            # copie
            self.ident = line.ident
            self.form = line.form
            self.lemma = line.lemma
            self.cat = line.cat
            self.catfine = line.catfine
            
            self.traits = line.traits
            self.head = line.head
            self.function = line.function
            self.other = line.other
            self.other2 = line.other2
            self.other3 = line.other3
            self.headObject = None
            self.dependants = []
            self.shiftedCols = line.shiftedCols
            

        else:        
            elems = line.split("\t")
            #print "eee", type(line)
            #print "ELEMS", elems
            self.shiftedCols = None
            if shift:
                self.shiftedCols = elems[:shift]
            self.ident = int(elems[shift])
            self.form = elems[shift+1] #.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            #if self.form != "_": self.form = self.form.replace("_", " ")
            #print "aaaaaaaaaaaaaaaaaa", type(self.form), self.form
            self.lemma = None
            if elems[shift+2] != "_":
                self.lemma = elems[shift+2]
                # Tilt rend qq fois le lemme déjà en UTF8 (et tout le reste en latin1)
                # donc il arrive que le lemme est doublement encodé
                #print "LEMMA", self.lemma
                try:
                    # ça marche, le lemme est donc doublement encodé
                    l = self.lemma.encode("latin1")
                    l2 = unicode(l, "utf-8")
                    #print l2
                    self.lemma = l2
                except (UnicodeDecodeError, UnicodeEncodeError):
                    #print "1 Unexpected error:", sys.exc_info()[0]
                    # normal, le lemme est correctement encodé, on ne fait rien
                    pass



            self.cat = elems[shift+3]
            self.catfine = elems[shift+4]

            self.traits = []
            traits = elems[shift+5]
            if traits and traits != "_":
                tt = traits.split("|")
                for t in tt:
                    self.traits.append(t.split("=", 1))

            if elems[shift+6] == "_": self.head = 0
            else: self.head = int(elems[shift+6])
            self.function = elems[shift+7] #.lower()
            if not self.function.startswith("__"):
                self.function = self.function.lower()
            if len(elems) > shift+8:
                self.other = elems[shift+8]
                if len(elems) > shift+9:
                    self.other2 = elems[shift+9]
                else:
                    self.other2 = "_"
                if len(elems) > shift+10:
                    self.other3 = elems[shift+10:]
                else:
                    self.other3 = None
            else:
                self.other = "_"
                self.other2 = "_"
                self.other3 = None

            self.headObject = None
            self.dependants = []

            #print "aaaa",self

            
        
#    def deps(self, ofp, indent=0):
#        #ofp.write("%s%s\n" % ("  "*indent, self))
#        ofp.write('%s<GRGS1 MOT="%s" DEP="%d" ARR="%d" CAT="%s" ID="%d" POS="%d"' % ("  "*indent,
#                                                                                     xmlify(self.form),
#                                                                                     self.ident-1,
#                                                                                     self.ident,
#                                                                                     self.catfine,
#                                                                                     self.ident,
#                                                                                     self.ident))
#        if (self.lemma):
#            ofp.write(' LEMMA="%s"' % xmlify(self.lemma))
#
#        if self.headObject:
#            elems = self.function.split(":", 1)
#            if len(elems) == 2:
#                ofp.write(' PI="%d" FONC="%s" REGLE="%s"' % (self.head,
#                                                             elems[0], elems[1]))
#            else:
#                ofp.write(' PI="%d" FONC="%s"' % (self.head,
#                                                  self.function))
#        ofp.write('>\n')
#
#        # des "traits" de la structVal, en fait uniquement un pseudotrait qui répète la form du terminal
#        # pour améliorer la lisibilité
#        #ofp.write('%s<EDT>\n' % ("  "*(indent+1)))
#        #ofp.write('%s<TRA NOM="FORM" VAL="%s"/>\n' % ("  "*(indent+2), xmlify(self.form)))
#        #ofp.write('%s</EDT>\n' % ("  "*(indent+1)))
#
#
#        #ofp.write('  %s<EDT TYPE="STRUCTVAL"><TRA NOM="t" VAL="v"/></EDT>\n' % ("  "*(indent)))
#        ofp.write('%s<TER  FLE="%s"' % ("  "*(indent+1),
#                                        xmlify(self.form)))
#
#        if (self.lemma):
#            ofp.write(' LEM="%s"' % xmlify(self.lemma))
#
#        ofp.write('>\n')
#
#
#        if self.traits or self.other != "_":
#            ofp.write('%s<EDT>\n' % ("  "*(indent+2)))
#            for t in self.traits:
#                if len(t) > 1:
#                    ofp.write('%s<TRA NOM="%s" VAL="%s"/>\n' % ("  "*(indent+3), t[0], t[1]))
#                else:
#                    ofp.write('%s<TRA NOM="%s" />\n' % ("  "*(indent+3), t[0]))
#
#            #print "sss %s" % self
#            if self.other != "_":
#                # dans 'universal dependencies' il y a des translitérations 
#                elems = self.other.split("|")
#                for e in elems:
#                    e1 = xmlify(e)
#                    kv = e1.split("=", 1)
#                    if len(kv) == 2:
#                        ofp.write('%s<TRA NOM="%s" VAL="%s"/>\n' % ("  "*(indent+3), kv[0], kv[1]))
#
#        
#            ofp.write('%s</EDT>\n' % ("  "*(indent+2)))
#        ofp.write('%s</TER>\n' % ("  "*(indent+1)))
#
#        for d in self.dependants:
#            d.deps(ofp, indent+1)
#
#        ofp.write('%s</GRGS1>\n' % ("  "*indent))




    def conllOut(self, ofp, tilt2ud=False, withShift=False):
        # tilt2ud: replace Tilt categories with those used in Univseral Dependencies
        traits = "_"
        if self.traits:
            traitslist = []
            for t in self.traits:
                traitslist.append(string.join(t, "="))
            traits = string.join(traitslist, "|")

        lemma = self.lemma
        if not lemma: lemma = u"_"
        #print "azazazz", type(self.form) #.encode("utf-8")
        #print "rrrr", sys.stdout
        #ofp.write("azazazzbb %s\n" % self.form)
        #cat = self.cat.encode("utf-8") + "QQQ"
        #origcat = self.cat.encode("utf-8")
        cat = self.cat + u"QQQ"
        origcat = self.cat
        if tilt2ud:
            #cat = cats.get(cat, "XXX"+cat)
            for regex,v in catRE.items():
                if regex.match(origcat):
                    cat = v
                    break
        else:
            cat = origcat

        if withShift and self.shiftedCols:
            ofp.write("%s\t" % string.join(self.shiftedCols, "\t"))

        rest = ""
        if self.other3:
            rest = "\t%s" % string.join(self.other3, "\t")
        ofp.write(u"%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s%s\n".encode("utf-8") % \
                  (self.ident,
                   self.form,
                   lemma,
                   cat,
                   self.catfine,
                   traits,
                   self.head,
                   self.function,
                   self.other,
                   self.other2,
                   rest
                   )
                  )
                   


    def out(self): 
        if self.lemma:
            le = self.lemma
        else:
            le = u""

        deps = u""
        deplist = []
        for x in self.dependants:
            deplist.append(x.ident)
        if len(deplist):
            deps = u" DEPS:%s" % deplist
        #print "ttt", dir(self.form)
        return u"{%d %s <%s>%s %s}" % (self.ident, self.catfine, self.form,
                                       deps, self.head #, le
                                     )

    def __unicode__(self):
	return self.__repr__()

    def __repr__(self):	
        if self.headObject:
            ho = u"HEAD:" + self.headObject.out()
        else:
            ho = u""
	

 	a = u"DEP:%s\t-%s->\t%s\t%s" \
               % (self.out(),
                  self.function,
                  ho,
                  self.error #, self.head
                  )
	#print a
        return a

    def getRoot(self, path):
        if self.head == 0:
            return self
        else:
            if self in path:
                #print "CERCLE ", path
                # CERCLE !
                return None
            else:
                path.add(self)
                return self.headObject.getRoot(path)

        

        
class Phrase:
    # la phrase entiere
    def __init__(self, words, number=-1):
        self.words = words
        self.txt = u""
        self.head = None
        self.number = number



        normaliseIDs(words)
	
        #print "zzzz", len(words)
	#print "zzzz", len(words)
        for w in words:
	    #print "www %s" % w.out().encode("utf-8")
            self.txt += w.form + u" "
            #print type(w.form)
            #print "eeee", w.form.encode("utf-8"), w.head
            
            if w.head == 0 or w.head >= 10000:
                if not self.head:
                    # tete de la phrase
                    self.head = w
            else:
                # on rajoute la tete au mot courant (la liste commence avec 1 et pas avec 0)
                #qq = u"%s" % w
                #print "ssss %s" % qq #.encode("utf-8")
                #print "zzzz", w.ident, w.head, w.catfine, w.function, w.form
                w.headObject = words[w.head-1]
                # on rajoute le mot courant au deps de sa tete
                w.headObject.dependants.append(w)

        # avec tilt on fait des coordinations différement:
        #  (A (B (et (C))))
        # la treebank fait
        #  (A (B) (et) (C))
        # il faut modifier la coordination Tilt en fonction de la treebank
        for w in words:
            if w.function.endswith(":ssCOORD_N_02"):
                if w.head != 0:
                    father = self.words[w.head-1]
                    if father:
                        # supprimer le mot de sa thete
                        w.headObject.dependants.remove(w)

                        # mettre une nouveau tete
                        w.head = father.head
                        w.headObject = words[father.head-1]
                        w.headObject.dependants.append(w)
                elif w.function.endswith(":COORD_N_01"):
                    father = self.words[w.head-1]
                    if father.head != 0:
                        grandfather = self.words[father.head-1];
                        if grandfather:
                            w.headObject.dependants.remove(w)

                            w.head = grandfather.head
                            w.headObject = words[grandfather.head-1]
                            w.headObject.dependants.append(w)

        #self.txtxml = xmlify(self.txt)
        #print self.txt

    def isHeadOf(self, headword, childword):
        # returns True if headword is (indirectly) head of childword
        if childword.headObject == None: return False
        if childword.headObject == headword: return True
        else:
            return self.isHeadOf(headword, childword.headObject)
        
    def isProjective(self):
        # convington 2001:
        # a tree is projectif iff every word in it comprises a continuous substring
        # a word comprises a continuous substring iff given any two words that it comprises, it also comprises all words between them
        # creer un dico id: Word
        words = {}
        for w in self.words:
            words[w.ident] = w

        self.unprojectiveWords = set()

        debug = False
        for w in self.words:
            if debug: print "word:", w.ident
            # check whether all words between current word and its head depend on the current word and its head
            if w.head == 0:
                if debug: print " the root!"
                continue # it's the head, cannot be non-proj

            if abs(w.head - w.ident) == 1:
                if debug: print " the neighbour to its!"
                continue # next/preceding word is head

            if w.ident < w.head :
                curident = w.ident+1
                while curident < w.head:
                    self.testnonproj(words, w, curident)
                    #if debug: print " A: testing %d and %d's head %d" % (curident, w.ident, w.head)
                    #rtc = self.isHeadOf(words[w.head], words[curident])
                    #if debug: print "  %d's head is %d's head" % (w.head, curident), rtc
                    #if not rtc:
                    #    if debug: print " B: testing %d and %d" % (curident, w.ident)
                    #    rtc = self.isHeadOf(w, words[curident])
                    #    if debug: print "  %d is %d's head" % (w.ident, curident), rtc
                    #if not rtc:
                    #    if debug: print " *** this words creates havoc", w.ident
                    #    self.unprojectiveWords.add(w)
                    curident += 1


            if w.ident > w.head :
                curident = w.ident-1
                while curident > w.head:
                    self.testnonproj(words, w, curident)
                    #if debug: print " A: testing %d and %d's head %d" % (curident, w.ident, w.head)
                    #rtc = self.isHeadOf(words[w.head], words[curident])
                    #if debug: print "  %d's head is %d's head" % (w.head, curident), rtc
                    #if not rtc:
                    #    if debug: print " B: testing %d and %d" % (curident, w.ident)
                    #    rtc = self.isHeadOf(w, words[curident])
                    #    if debug: print "  %d is %d's head" % (w.ident, curident), rtc
                    #if not rtc:
                    #    if debug: print " *** this words creates havoc", w.ident
                    #    self.unprojectiveWords.add(w)
                    curident -= 1

        #return True
        return len(self.unprojectiveWords) == 0

    def testnonproj(self, words, w, curident):
        debug = False
        if debug: print " A: testing %d and %d's head %d" % (curident, w.ident, w.head)
        rtc = self.isHeadOf(words[w.head], words[curident])
        if debug: print "  %d's head is %d's head" % (w.head, curident), rtc
        if not rtc:
            if debug: print " B: testing %d and %d" % (curident, w.ident)
            rtc = self.isHeadOf(w, words[curident])
            if debug: print "  %d is %d's head" % (w.ident, curident), rtc
        if not rtc:
            if debug: print " *** this words creates havoc", w.ident
            self.unprojectiveWords.add(w)


    def projectivize(self, unprojectiveWords):
        # change deprels to make the tree projective: We attach a non-projective word to the head of it's head and so on
        # until it is ok. We then modify the deprel from X to A:B:X
        # commas must have been corrected in before !!

        # creer un dico id: Word
        words = {}
        for w in self.words:
            words[w.ident] = w
        for w in unprojectiveWords:
            # replace word's head with head's head and check
            head = w.headObject
            headshead = head.headObject
            w.head = headshead.ident
            #print >> sys.stderr, "w %d had head %d and gets %d" % (w.ident, head.ident, w.head)
            
            w.function = head.function + "=" + w.function
            w.headObject = headshead
            head.dependants.remove(w)
            headshead.dependants.append(w)
            

    def deprojectivize(self):
        # change deprels A=B=C into C by trying do detach word from its head and searching a word going down deprel A and B
        # may not be possible, if prediction went wrong
        words = {}
        for w in self.words:
            words[w.ident] = w

        for w in self.words:
            if w.function.find("=") >= 0:
                #print >> sys.stderr, "W:", w.ident, w.function
                deprels = w.function.split("=")
                head = w.headObject
                word = head
                newfunction = deprels
                lastchild = None
                for deprel in deprels[:-1]:
                    #print >> sys.stderr, "deprel:", deprel
                    child = self.finddep(word, deprel)
                    if child == None: break
                    lastchild = child
                    #print >> sys.stderr, "child:", child.ident
                    word = child
                    newfunction.remove(deprel)
                #print >> sys.stderr, "lastchild:", lastchild.ident
                if lastchild:
                    # attach w to child
                    lastchild.dependants.append(w)
                    w.headObject = lastchild
                    w.head = lastchild.ident
                    head.dependants.remove(w)
                    w.function = newfunction[-1] #string.join(newfunction, "=")

    def finddep(self, w, deprel):
        for child in w.dependants:
            if child.function == deprel:
                return child
        return None

    def ooisProjective(self):
        # rend True si la phrase est projective (voir Covington 2001: A Fundemental Algorithm for Dependency Parsing)
        # un mot X entre deux mots A et B doivent dépendre (directement ou indirectement) de un ces deux mots
        # ou tous les mots entre une tête et son dépendant doivent dépendre (directement ou indirectement) de un ces deux mots
        #print self.__repr__()
        #print "%s" % self
        # creer un dico id: Word
        words = {}
        for w in self.words:
            words[w.ident] = w

        self.unprojectiveWords = set()
        for w in self.words:
            if not w.headObject: continue # root n'a pas de tête
            #print "%s" % w
            dist = abs(w.ident-w.headObject.ident)
            #print dist, w.ident, w.headObject.ident

            if dist > 1:
                startix = min(w.ident, w.headObject.ident)
                leftWord = words[startix]
                endix = max(w.ident, w.headObject.ident)
                rightWord = words[endix]

                #print "from/to %d %d, dist %d" % (w.ident, w.headObject.ident, dist)
                #print " startix %d, endix %d" % (startix, endix)
                #print " FROM %s" % leftWord
                #print " TO   %s" % rightWord
                
                for ix in range(dist-1):
                    # check heads of current word (must end at w.ident or w.headObject.ident)
                    curWord = words[startix+ix+1]
                    #print "  IN BETWEEN: %d  %s" % (startix+ix+1, curWord)
                    curHead = curWord.headObject

                    while True:
                        #print " CURHEAD %s" % curHead
                        if not curHead:
                            #print "NON PROJECTIVE %s" % curWord.form
                            self.unprojectiveWords.add(curWord)
                            #return False
                            break
                        # si la tete du mot courant est leftWord ou rightWord
                        if curHead.ident == leftWord.ident:
                            #print "OK l"
                            break
                        elif curHead.ident == rightWord.ident:
                            #print "OK r"
                            break
                        curHead = curHead.headObject
        #return True
        return len(self.unprojectiveWords) == 0

    def isTree(self):
        # pas de circle, et tout arriver à la tête
        for w in self.words:
            if w.head == 0: continue
            path = set()
            root = w.getRoot(path)
            if root == None: return False
        return True

    def makeCommasProjective(self, use_set=True):
        #for w in self.unprojectiveWords:
        for w in self.words:
            if use_set and not w in self.unprojectiveWords: continue

            if w.form == "," or (w.cat == "PUNCT" and w.form not in "()"):
                if len(w.dependants) != 0:
                    ids = []
                    for d in w.dependants: ids.append(d.ident)
                    print >> sys.stderr, "Comma %d with depdendents %s in sentence %d" % (w.ident, ids, self.number)
                    continue
            
            w.dependants = []

            if w.form == "," or (w.cat == "PUNCT" and w.form not in "()"):

                dist = abs(w.ident - w.head)
                #print >> sys.stderr, "zzzz", w.ident, dist
                if dist > 1:
                    if w.ident != 1:
                        w.head = w.ident - 1
                        w.headObject = self.words[w.ident - 2]
                    else:
                        w.head = w.ident + 1
                        w.headObject = self.words[w.ident]

        #print "eee", self

        for w in self.words:
            if w.headObject:
                w.headObject.dependants.append(w)
                
    def __len__(self):
        return len(self.words)

    def size(self):
        return len(self.words)
    
    def __repr__(self):
        out = self.txt
        #print type(out)
        for w in self.words:
            
            out += u"\n\t%s" % w
        return out


    def getFirstHead(self):
        for word in self.words:
            if word.head == 0:
                return word
        # pas de tete trouver, on rend le dernier mot
        return word


    def separatePartialTrees(self):
        # parcourir les mots jusq'à un root,
        # chercher les autres feuilles qui dépendent de cette racine
        # extrair cet arbre partiel

        independentHeads = []
        partialTrees = []        
        for word in self.words:
            if word.head == 0:
                # root
                #if len(word.dependants) == 0:
                #    words = [word]
                #    words.sort(sortWord)
                #    normaliseIDs(words)
                #    p = Phrase(words)
                #    partialTrees.append(p)
                #else:
                independentHeads.append(word)
                    
        #print "IHs", len(independentHeads)
        for ih in independentHeads:
            #print "IH\t", ih, len(ih.dependants)
            if len(ih.dependants) == 0:
                words = [ih]
                words.sort(sortWord)
                normaliseIDs(words)
                p = Phrase(words)
                partialTrees.append(p)
            else:
                firstindex = ih.ident
                lastindex = ih.ident
                modif = True
                while modif:
                    modif = False
                    #print "SSS", firstindex, lastindex
                    for dep in self.words[firstindex-1].dependants:
                        #print "  first", dep
                        if dep.ident < firstindex:
                            firstindex = dep.ident
                            modif = True
                    for dep in self.words[lastindex-1].dependants:
                        #print "  last", dep
                        if dep.ident > lastindex:
                            modif = True
                            lastindex = dep.ident
                #print "RRRR", firstindex, lastindex
                words = self.words[firstindex-1:lastindex]
                print len(words), words
                normaliseIDs(words)
                p = Phrase(words)
                partialTrees.append(p)
        

        #print "PTs"
        #for pt in partialTrees:
        #    print "PT",pt
        #print
        return partialTrees

        
    def conllOut(self, ofp=sys.stdout, tilt2ud=False, withShift=False):
        for w in self.words:
            w.conllOut(ofp, tilt2ud, withShift)
        ofp.write("\n")


#    def tiltout(self, ofp=sys.stdout, codage="utf-8"):
#        ofp.write("<?xml version=\"1.0\" encoding=\"%s\"?>\n" % codage)
#        ofp.write("<TLT>\n  <PARA>\n    <PHR TXT=\"%s\">\n" % self.txt)
#        ofp.write("      <ANALYSES_DEP SOL=\"Totale\">\n")
#        # si on des arbres partiels
#        #phs = self.separatePartialTrees()
#        # pour les treebanks corrects
#        phs = [self]
#        for ph in phs:
#            #print "zzz", ph.words[0].ident, ph.words[-1].ident
#            ofp.write("        <TRONCON DEP=\"%d\" ARR=\"%d\">\n" % (ph.words[0].ident, ph.words[-1].ident))
#            ofp.write("          <ANALYSE_DEP DEP=\"%d\" ARR=\"%d\" ID=\"001\" score=\"1\">\n" % (ph.words[0].ident, ph.words[-1].ident))
#            ph.head.deps(ofp, indent=6)
#            ofp.write("          </ANALYSE_DEP>\n")
#            ofp.write("        </TRONCON>\n")
#
#        # on affiche que le premier arbre (partiel/complet)
#        #ofp.write("        <TRONCON DEP=\"0\" ARR=\"%d\">\n" % len(self.words))
#        #ofp.write("          <ANALYSE_DEP DEP=\"0\" ARR=\"%d\" ID=\"001\" score=\"1\">\n" % len(self.words))
#        ##for w in self.words:  ofp.write("%s\n" % w)
#        #self.head.deps(ofp, indent=6)
#        #ofp.write("          </ANALYSE_DEP>\n")
#        #ofp.write("        </TRONCON>\n")
#        ofp.write("      </ANALYSES_DEP>\n")
#        ofp.write("    </PHR>\n  </PARA>\n</TLT>\n")


class ConllDocSentencewise:
    def __init__(self, fn=None, encoding="utf-8", shift=0):
        #if fn:
        self.ifp = codecs.open(fn, "r", encoding=encoding)
        self.shift = shift
        self.countphrase = 0
        #self.phrases = self.read(ifp, shift)
        #elif text:
        #    ifp = StringIO.StringIO(text)
        #    self.phrases = self.read(ifp, shift)

    def next(self):
        #ifp = open(fn)
        self.countphrase += 1

        words = [] # [word-instance] les lignes d'une phrase
        for line in self.ifp:            
            line = line.strip()
            #print "LINE", self.shift, line #.encode("utf-8")
            if line:
                if line[0] == "#":
                    continue
                if line.split("\t", self.shift+1)[self.shift].find("-") > -1:
                    continue
                wd = Word(line, self.shift)
                #print "rr", wd
                words.append(wd)
            else:
                if len(words):
                    break
                #if len(words) > 0:
                #    countphrase += 1
                #    phrases.append(Phrase(words))

        #print u"aaaaaa %d %s" %( self.countphrase, words[0])
        #words[1].ident, words[1].cat
        return Phrase(words, self.countphrase)


    def nextNoParse(self):
        #ifp = open(fn)
        self.countphrase += 1

        words = [] # [word-instance] les lignes d'une phrase
        for line in self.ifp:            
            line = line.strip()
            #print "LINE", line #.encode("utf-8")
            if line:
                if line[0] == "#":
                    continue
                if line.split("\t", self.shift+1)[self.shift].find("-") > -1:
                    continue
                #wd = Word(line, self.shift)
                #print "rr", wd
                words.append(line)
            else:
                if len(words):
                    break
                #if len(words) > 0:
                #    countphrase += 1
                #    phrases.append(Phrase(words))

        #print u"aaaaaa %d %s" %( self.countphrase, words[0])
        #words[1].ident, words[1].cat
        #return Phrase(words)
        return words

    def readAll(self, total, last, indexes):
        # read all sentences which index is in indexes
        self.sentences = []
        for ix in range(total):
            if ix > last: break
            
            if not ix in indexes:
                sent1 = self.nextNoParse()
            else:
                self.sentences.append(self.nextNoParse())
            if ix % 10000 == 0:
                sys.stderr.write("%d/%d sentences read %d kept\r" % (ix, total, len(self.sentences)))
        self.ifp.close()


class ConllDoc:
    def __init__(self, fn=None, encoding="utf-8", text=None, shift=0, verbose=False):
        self.verbose = verbose
        if fn:
            ifp = codecs.open(fn, "r", encoding=encoding)
            self.phrases = self.read(ifp, shift)
        elif text:
            ifp = StringIO.StringIO(text)
            self.phrases = self.read(ifp, shift)

    def read(self, ifp, shift):
        #ifp = open(fn)
        countphrase = 0
        phrases = []
        words = [] # [word-instance] les lignes d'une phrase
        for line in ifp.readlines():
            line = line.strip()
            #print "LINE", line.encode("utf-8")
            if line:
                if line[0] == "#":
                    continue
                if line.split("\t", shift+1)[shift].find("-") > -1:
                    continue
                wd = Word(line, shift)
                #print "rr", wd
                words.append(wd)
            else:
                if len(words) > 0:
                    countphrase += 1
                    phrases.append(Phrase(words))
                    if self.verbose and countphrase % 500 == 0:
                        sys.stderr.write("%d sentences read\r" % countphrase)
                words = []
        if self.verbose:
            sys.stderr.write("%d sentences read\n" % countphrase)
        ifp.close()

        # stocker la dernière phrase
        if len(words) > 0:
            phrases.append(Phrase(words))

        return phrases

        
if __name__ == "__main__":
    import sys

    from optparse import OptionParser

    parser = OptionParser(usage="usage: %prog [options]", description="normaliser les fichiers CONLL")
    parser.add_option("-r", dest="replace", action="store_true", default=False,  help="replace Tilt categories by UD categories")
    parser.add_option("-e", "--encoding", dest="encoding", default="utf-8", help="encoding of CONLL file")
    parser.add_option("-c", "--justcount", dest="justcount", action="store_true", default=False, help="just count sentences")
    parser.add_option("-R", "--reshuffleTo", dest="reshuffle", default=None, help="reshuffle sentences")



    (options, comargs) = parser.parse_args()
    if len(sys.argv) < 2 or len(comargs) < 1:
        parser.print_help()
    else:
        if options.justcount:
            cd = ConllDocSentencewise(fn=comargs[0], encoding=options.encoding)
            ct = 0
            while True:
                p = cd.next()
                if len(p):
                    ct += 1
                else:
                    break
            print "%s\t%d" % (comargs[0], ct)
            
        elif options.reshuffle:
            import random
            sentences = []
            for fn in comargs:
                cd = ConllDoc(fn=fn, encoding=options.encoding)
                sentences.extend(cd.phrases)
            random.shuffle(sentences)
            ofp = codecs.open(options.reshuffle, "w", encoding="utf-8")
            for s in sentences:
                s.conllOut(ofp=ofp)
            ofp.close()
        else:
            # normaliser les IDq
            cd = ConllDoc(fn=comargs[0], encoding=options.encoding)

            for p in cd.phrases:
                p.conllOut(tilt2ud=options.replace)
