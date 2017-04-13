#!/bin/bash

TEST=$1
LANG=$2

# TODO: change as needed
export LD_LIBRARY_PATH="/home/langnat/conll2017/bistparser/cnn-v1-gpu/pycnn"
echo ">>>" $LD_LIBRARY_PATH
# the temp directory for the run
TMPDIR=$(mktemp -d)

BASEPATH=/mnt/RAID0SHDD2X1TB/Orange-Deskin

OUTPATH=$BASEPATH/output

PYSCRIPTROOT=$BASEPATH/py

BISTROOT=$BASEPATH/bistparser/barchybrid

# TODO: change as needed
DATAPATH=/home/langnat/conll2017/data

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
        echo $@
        cat $@ | sort -u
}

# deprojectivises output from prediction with BistParser
function deprojectivise() {
        INFILE=$1
        $PYSCRIPTROOT/projectivise.py -d $INFILE
}

# prediction function
function predict() {

        # incoming file (to be predicted)
        INFILE=$1

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
       
        # prediction
        # this path is needs to be adapted for individual system
	pushd $BISTROOT > /dev/null

        python src/parser.py --cnn-mem 4000 --predict \
                --outfile $TMPDIR/result1.conllu \
                --model $MODEL \
                --params $PARAMS \
                $VECTORS \
                --test $INFILE

        popd $BISTROOT > /dev/null

        # check whether we need to deprojectivise
        COUNTPSEUDOPROJ=$(cut -f8 $TMPDIR/result1.conllu | grep "=" | wc -l)
        if [ $COUNTPSEUDOPROJ -ne 0 ]; then
                deprojectivise $TMPDIR/result1.conllu > $TMPDIR/result-deproj.conllu
        else
                cp $TMPDIR/result1.conllu $TMPDIR/result-deproj.conllu
        fi

        # reinsert lines with [n-m] or [n.1]
        #reinsiert $TMPDIR/result-deproj.conllu $OUTFILE
        pyhton $PYSCRIPTROOT/reinsert.py $TEST $TMPDIR/result-deproj.conllu > $TMPDIR/result-deproj-reinsert.conllu

}

# cleaning CoNLL input of comments and compound representations
echo "Cleaning ..."
CLEANTEST=$TMPDIR/$LANG.clean.test.conll
cat $TEST | cleanconllu > $CLEANTEST

# extract surface forms from input
echo "Getting Form List ..."
FORMLIST=$TMPDIR/$LANG.forms.txt
formslist $CLEANTEST > $FORMLIST

# extract lemmas from input
echo "Getting Lemma List ..."
LEMLIST=$TMPDIR/$LANG.lemmas.txt
lemmalist $CLEANTEST > $LEMLIST

# create word list
echo "Generating Word List ..."
WORDLIST=$TMPDIR/$LANG.words.txt
#ALLWORDS=$DATAPATH/$LANG/allwords.txt
ALLWORDS=$DATAPATH/allwords.txt
wordlist $ALLWORDS $FORMLIST $LEMLIST > $WORDLIST

EXVECTORS=
if [ "$3" != "" ]; then
	EXVECTORS=$3
fi

# predict
echo "Predicting ..."
predict $CLEANTEST $MODELPATH/*.model_??? $MODELPATH/params.pickle $WORDLIST $EXVECTORS

cp $TMPDIR/result-deproj-reinsert.conllu $OUTPATH/$LANG.output.conllu

# clean up
rm -rf $TMPDIR

