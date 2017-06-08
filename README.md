# Orange-Deskiñ
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


## How to install

This version of BistParser still uses the legacy library cnn
(https://github.com/clab/cnn-v1), which has to be adapted in order to allow
to load only word-embeddings of words seen in the text to parse

In order to get it running
* get cnn-v1
    git clone https://github.com/clab/cnn-v1

* get eigen 
    hg clone https://bitbucket.org/eigen/eigen/
* replace `cnn/model.h' by the file in cnn-modifs
* compile
    cd cnn-v1
    mkdir build
    pushd build
    cmake .. -DEIGEN3_INCLUDE_DIR=../eigen
    popd  
    make
* modify pycnn/setup.py (directory "`../../cnn`" should be "`../../cnn-v1`")
* compile python interface
    cd pycnn
    make install

## train models

You need external word embeddings produced with `word2vec`.
If you want to use pseudo-projectivisation, pass you treebanks trough
`py/projectivise.py`:
    py/projectivise.py -c train.conllu > train-pojective.conllu

If your treebank file contains comments or multi-word lines (`2-3 ...`), you must delete
them

set environment variable to find cnn-python-library
    export LD_LIBRARY_PATH=PATH/TO/cnn-v1/pycnn
  

run training
    python bistparser/barchybrid/src/parser.py \
      --cnn-mem 4000  \
      --outdir /PATH/TO/OUTDIR \
      --train train-projective.conllu \
      --dev dev-projective.conllu \
      --epochs 20 --lstmdims 125 \
      --lstmlayers 2 --bibi-lstm \
      --k 3 --usehead --userl \
      --extrn word2vec.cbow.bin \
      --extrnFilter train-words-to-load.txt \
      [--hidden 50]


The file `train-words-to-load.txt` contains the words to load from word2vec is created by the
following command:
    cut -f2 train-projective.conllu | sort -u > forms.txt
    cut -f3 train-projective.conllu | sort -u > lemmas.txt
    cat forms.txt lemmas.txt | perl -CSD -ne 'print lc' | sort -u > train-words-to-load.txt.txt

The option `--extrnFilter` is facultative. But since the word-embeddings
files contain millions of words (depending of the configuration of
`word2vec`) and the train treebank contains only a subset of those, it saves
time and memory usage to load only word embeddings of words needed.


## use models
Find the best model which the training has produced. It will be one of
`/PATH/TO/OUTDIR/barchybrid.model_*`

    export LD_LIBRARY_PATH=PATH/TO/cnn-v1/pycnn

The file `test-words-to-load.txt` contains the words of the text file
    cut -f2 test-projective.conllu | sort -u > forms.txt
    cut -f3 test-projective.conllu | sort -u > lemmas.txt
    cat forms.txt lemmas.txt | perl -CSD -ne 'print lc' | sort -u > test-words-to-load.txt.txt


    python bistparser/barchybrid/src/parser.py \
      --cnn-mem 4000 --predict \
      --outfile result.conllu \
      --test test-projective.conllu \
      --model /PATH/TO/OUTDIR/barchhybrid.model_NNN \
      --params /PATH/TO/OUTDIR/params.pickle \
      --k 3 --usehead --userl \
      --extrn word2vec.cbow.bin \
      --extrnFilter train-words-to-load.txt \
      --extrnFilterNew test-words-to-load.txt \

De-projectivise output:
    py/projectivise.py -d result.conllu > result-deprojectivised.conllu


## References

 * Kiperwasser, E.; Goldberg, Y. (2016): [Simple and Accurate Dependency Parsing Using Bidirectional LSTM Feature Representations](https://www.transacl.org/ojs/index.php/tacl/article/viewFile/885/198), arXiv preprint arXiv:1603.04351.
 * Heinecke, J.; Asadullah, M. (2017): Multi-Model and Crosslingual Dependency Analysis. In: Proceedings of the CoNLL 2017 Shared Task; Multilingual Parsing from Raw Text to Universal Dependencies. ACL


