#!/bin/bash

TEST=$1
LANG=$2

BISTROOT=/home/langnat/conll2017/bistparser/barchybrid
PARSERPATH=$BISTROOT/src/parser.py
MODELPATH=/home/langnat/conll2017/data/$LANG

# cleaning CoNLL text of comments and compound representations
function cleanconllu() {
        grep -v "^#" | grep -P -v '^\d+[\.-]'
}

# extract surface forms from a CoNLL text
function formslist() {
        INFILE=$1
        cut -f2 $INFILE | sort -u
}

# extract lemmas from a CoNLL text
function lemmalist() {
        INFILE=$1
        cut -f3 $INFILE | sort -u
}

# generate word list
function wordlist() {
        WORDS=$1
        LEMMAS=$2
        cat $WORDS $LEMMAS | sort -u
}

# deprojectivises output from prediction with BistParser
function deprojectivise() {
        INFILE=$1
        /home/langnat/conll2017/py/projectivise.py -d $INFILE
}

function predict() {
        # incoming file (to be predicted)
        INFILE=$1

        # result (to be evaluated)
        #OUTFILE=$2

        # model to use
        MODEL=$2
        
        # BistParser parameters to use
        PARAMS=$3
	
	# word list file
	WORDS=$4

        # word embeddings to use
	VECTORS=
	if [ "$5" != "" ]; then
        	VECTORS="--extrn $5 --extrnFilter $WORDS"
	fi

        # create a temporary directory
        TMPDIR=$(mktemp -d)
       
        # prediction
	export LD_LIBRARY_PATH="/home/langnat/conll2017/bistparser/cnn-v1-gpu/pycnn"
	echo $LD_LIBRARY_PATH
	pushd $BISTROOT
        python src/parser.py --cnn-mem 4000 --predict \
                --outfile $TMPDIR/result1.conllu \
                --model $MODEL \
                --params $PARAMS \
                $VECTORS \
                --test $INFILE

        # check whether we need to deprojectivise
        COUNTPSEUDOPROJ=$(cut -f8 $TMPDIR/result1.conllu | grep "=" | wc -l)
        if [ $COUNTPSEUDOPROJ -ne 0 ]; then
                deprojectivise $TMPDIR/result1.conllu > $TMPDIR/result-deproj.conllu
        else
                cp $TMPDIR/result1.conllu $TMPDIR/result-deproj.conllu
        fi

        # reinsert lines with [n-m] or [n.1]
        # TODO
        #reinsiert $TMPDIR/result-deproj.conllu $OUTFILE

        # clean up
        #rm -rf $TMPDIR
}


TMPWDIR=$(mktemp -d)

# cleaning CoNLL input of comments and compound representations
echo "Cleaning ..."
CLEANTEST=$TMPWDIR/$LANG.clean.test.conll
cat $TEST | cleanconllu > $CLEANTEST

# extract surface forms from input
echo "Getting Form List ..."
FORMLIST=$TMPWDIR/$LANG.forms.txt
formslist $CLEANTEST > $FORMLIST

# extract lemmas from input
echo "Getting Lemma List ..."
LEMLIST=$TMPWDIR/$LANG.lemmas.txt
lemmalist $CLEANTEST > $LEMLIST

# create word list
echo "Generating Word List ..."
WORDLIST=$TMPWDIR/$LANG.words.txt
wordlist $FORMLIST $LEMLIST > $WORDLIST

EXVECTORS=
if [ "$3" != "" ]; then
	EXVECTORS=$3
fi

# predict
predict $CLEANTEST $MODELPATH/*.model_??? $MODELPATH/params.pickle $WORDLIST $EXVECTORS

# clean up
#rm -rf $TMPWDIR

