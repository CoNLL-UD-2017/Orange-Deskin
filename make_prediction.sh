#!/bin/bash

if [ $# -lt 3 ]; then
	echo "usage $0 test.conllu language-code outfile"
	exit 1
fi


TEST=$1
LANG=$2
OUTFILE=$3


HOSTNAME=$(hostname)


if [ "$HOSTNAME" == "tira-ubuntu" ]; then
	export LD_LIBRARY_PATH=/home/Orange-Deskin/conll2017/cnn-v1-gpu/pycnn
	BASEPATH=/home/Orange-Deskin/conll2017/Orange-Deskin
	DATAPATH=$BASEPATH/data
elif [ "$HOSTNAME" == "yd-jeuh6401" ]; then
	export LD_LIBRARY_PATH=/home/jeuh6401/SemanticData/bist-parser/cnn-v1-gpu/pycnn
	BASEPATH=/home/jeuh6401/conll2017/Orange-Deskin
	DATAPATH=$BASEPATH/data
else
	export LD_LIBRARY_PATH="/home/langnat/conll2017/bistparser/cnn-v1-gpu/pycnn"
	BASEPATH=/mnt/RAID0SHDD2X1TB/Orange-Deskin
	DATAPATH=/home/langnat/conll2017/data
fi



# the temp directory for the run
TMPDIR=$(mktemp -d)

#OUTPATH=$BASEPATH/output
PYSCRIPTROOT=$BASEPATH/py
BISTROOT=$BASEPATH/bistparser/barchybrid
MODELPATH=$DATAPATH/$LANG


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

# generate word list (lowercase)
function wordlist() {
        cat $@ | perl -CSD -ne 'print lc'
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
	
	# word list file words known during training
	WORDS=$4

	# words read in document to parse
	NEWWORDS=$5

        # word embeddings to use
	VECTORS=
	if [ "$6" != "" ]; then
        	VECTORS="--extrn $6 --extrnFilter $WORDS --extrnFilterNew $NEWWORDS"
	fi
       
        # prediction
        # this path is needs to be adapted for individual system
	pushd $BISTROOT > /dev/null

        #python src/parser.py --cnn-mem 4000 --predict 
        python src/parse_1by1.py --cnn-mem 4000 --predict \
                --outfile $TMPDIR/result1.conllu \
                --model $MODEL \
                --params $PARAMS \
                $VECTORS \
                --test $INFILE

        popd > /dev/null

        # check whether we need to deprojectivise
        COUNTPSEUDOPROJ=$(cut -f8 $TMPDIR/result1.conllu | grep "=" | wc -l)
        if [ $COUNTPSEUDOPROJ -ne 0 ]; then
                deprojectivise $TMPDIR/result1.conllu > $TMPDIR/result-deproj.conllu
        else
                cp $TMPDIR/result1.conllu $TMPDIR/result-deproj.conllu
        fi

        # reinsert lines with [n-m] or [n.1]
        #reinsiert $TMPDIR/result-deproj.conllu $OUTFILE
        python $PYSCRIPTROOT/reinsert.py $TEST $TMPDIR/result-deproj.conllu > $TMPDIR/result-deproj-reinsert.conllu

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
ALLWORDS=$DATAPATH/$LANG/allwords.txt
wordlist $FORMLIST $LEMLIST > $WORDLIST

# TODO make it work without and with 300 dims
#EXVECTORS=$MODELPATH/*500-dim.10-win.cbow.bin

# find correct vectors file
VECTORFILE=$($PYSCRIPTROOT/readparamspickle.py $MODELPATH/params.pickle  external_embedding | gawk -F / '{print $NF}')
if [ "$VECTORFILE" != "None" ]; then
	EXVECTORS=$MODELPATH/$VECTORFILE
fi

# predict
echo "Predicting ..."
predict $CLEANTEST $MODELPATH/*.model_??? $MODELPATH/params.pickle $ALLWORDS $WORDLIST $EXVECTORS

# copy result in output folder
#cp $TMPDIR/result-deproj-reinsert.conllu $OUTPATH/$LANG.output.conllu
cp $TMPDIR/result-deproj-reinsert.conllu $OUTFILE

# evaulation for testing
#$PYSCRIPTROOT/evaluation_script/conll17_ud_eval.py --weights $PYSCRIPTROOT/evaluation_script/weights.clas $TEST $TMPDIR/result-deproj-reinsert.conllu

# clean up
#rm -rf $TMPDIR

