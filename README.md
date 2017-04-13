# Orange-Deskin
CoNLL 2017 Shared Task Team Orange-Deskin (Orange/OLPS/CONTENT/DESKIN)

We use a modified version of BistParser
(https://github.com/elikip/bist-parser, old version which uses CNN
library (https://github.com/clab/cnn-v1)), which
  * only outputs dependency trees with a unique root
  * uses pseudo projectivisation
  * can deal with conllu (comments, 2-3 and 5.1 lines)
  * filter word embeddings: we only load vectors of words needed for the current corpus
  * changed CNN to accept different number of word embeddings during
  training and prediction

Everything is trained exclusively on Universial Dependency Conll2017 treebanks.
Word embeddings have been calculated on corpora taken from https://lindat.mff.cuni.cz/repository/xmlui/bitstream/handle/11234/1-1989


