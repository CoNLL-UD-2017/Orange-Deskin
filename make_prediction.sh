#!/bin/bash


LC_ALL=en_US.UTF-8
LANG=en_US.UTF-8
LANGUAGE=en_US.UTF-8

# TODO
# if language is non known, take "mix" with forms rempalce by CPOS+rand(), 
# lemmas deleted and POS replaced by CPOS


if [ $# -lt 3 ]; then
	echo "usage $0 test.conllu language-code outfile"
	exit 1
fi



TEST=$1
LANGUE=$2
OUTFILE=$3

HOSTNAME=$(hostname)
NOW=$(date '+%Y.%m.%d %H:%M')


echo -e "\nProcessing language: $LANGUE, start: $NOW"
echo -e "\nProcessing language: $LANGUE, start: $NOW" 1>&2



if [ "$HOSTNAME" == "tira-ubuntu" ]; then
	export LD_LIBRARY_PATH=/home/Orange-Deskin/conll2017/cnn-v1-gpu/pycnn
	BASEPATH=/home/Orange-Deskin/conll2017/Orange-Deskin
	DATAPATH=$BASEPATH/data
	MODELSPATH=$BASEPATH/models
elif [ "$HOSTNAME" == "yd-jeuh6401" ]; then
	export LD_LIBRARY_PATH=/home/jeuh6401/SemanticData/bist-parser/cnn-v1-gpu/pycnn
	BASEPATH=/home/jeuh6401/conll2017/Orange-Deskin
	DATAPATH=$BASEPATH/data
	MODELSPATH=$BASEPATH/models
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
EMBEDDINGSPATH=$DATAPATH/$LANGUE
MODELPATH=$MODELSPATH/$LANGUE

if [ "$HOSTNAME" == "yd-jeuh6401" ]; then
    EMBEDDINGSPATH=/data/SemanticData/conll2017/embeddings
fi

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
	#pushd $BISTROOT > /dev/null

	echo python $BISTROOT/src/parse_1by1.py --cnn-mem 4000 --predict \
                --outfile $TMPDIR/result1.conllu \
                --model $MODEL \
                --params $PARAMS \
                $VECTORS \
                --test $INFILE


        #python src/parser.py --cnn-mem 4000 --predict 
        python $BISTROOT/src/parse_1by1.py --cnn-mem 4000 --predict \
                --outfile $TMPDIR/result1.conllu \
                --model $MODEL \
                --params $PARAMS \
                $VECTORS \
                --test $INFILE

        #popd > /dev/null

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
CLEANTEST=$TMPDIR/$LANGUE.clean.test.conll
cat $TEST | cleanconllu > $CLEANTEST


if [ ! -d $MODELSPATH/$LANGUE ]; then
	# check whether we know language without specification (such as _partut)
	LGPREFIX=$(echo $LANGUE | cut -d_ -f1)
	#echo "prefix $LGPREFIX"
	if [ -d $MODELSPATH/$LGPREFIX ]; then
		LANGUE=$LGPREFIX
		echo "unknown language variation, using $LANGUE"
		EMBEDDINGSPATH=$DATAPATH/$LANGUE
		MODELPATH=$MODELSPATH/$LANGUE
	else
		#LANGUE=mix2_random
		LANGUE=mix2B
		echo "unknown language, using $LANGUE"
		CLEANTEST2=$TMPDIR/$LANGUE.clean.test.empty.conll
		# delete lemmas, replace forms by CPOS (plus random number for NOUN, VERB and ADJ) and replace POS by CPOS
		#cat $CLEANTEST | gawk -F '\t' 'OFS="\t" {if (NF > 6) {if ($4 == "NOUN" || $4 == "VERB" || $4 == "ADJ") print $1, sprintf("%s%d", $4, rand()*50), "_", $4,$4,$6,$7,$8,$9,$10; else print $1, $4, "_", $4,$4,$6,$7,$8,$9,$10;} else print ""}' > $CLEANTEST2
		# delete lemmas, replace forms by CPOS (except NOUNS, VERB and ADJ) and replace POS by CPOS
		cat $CLEANTEST | gawk -F '\t' 'OFS="\t" {if (NF > 6) {if ($4 == "NOUN" || $4 == "VERB" || $4 == "ADJ") print $1, $2, "_", $4,$4,$6,$7,$8,$9,$10; else print $1, $4, "_", $4,$4,$6,$7,$8,$9,$10;} else print ""}' > $CLEANTEST2
		CLEANTEST=$CLEANTEST2
		EMBEDDINGSPATH=$DATAPATH/$LANGUE
		MODELPATH=$MODELSPATH/$LANGUE
	fi
else
	# check whether input text needs to be "normalised"
	if [ -f $MODELSPATH/$LANGUE/NOWORDS ]; then
		echo "replacing forms by CPOS for $LANGUE"
		CLEANTEST2=$TMPDIR/$LANGUE.clean.test.empty.conll
		cat $CLEANTEST | gawk -F '\t' 'OFS="\t" {if (NF > 6) {if ($4 == "NOUN" || $4 == "VERB" || $4 == "ADJ") print $1, $2, "_", $4,$4,$6,$7,$8,$9,$10; else print $1, $4, "_", $4,$4,$6,$7,$8,$9,$10;} else print ""}' > $CLEANTEST2
		CLEANTEST=$CLEANTEST2
	fi
fi


# extract surface forms from input
echo "Getting Form List ..."
FORMLIST=$TMPDIR/$LANGUE.forms.txt
formslist $CLEANTEST > $FORMLIST

# extract lemmas from input
echo "Getting Lemma List ..."
LEMLIST=$TMPDIR/$LANGUE.lemmas.txt
lemmalist $CLEANTEST > $LEMLIST

# create word list
echo "Generating Word List ..."
WORDLIST=$TMPDIR/$LANGUE.words.txt
ALLWORDS=$MODELSPATH/$LANGUE/allwords.txt
wordlist $FORMLIST $LEMLIST > $WORDLIST

# TODO make it work without and with 300 dims
#EXVECTORS=$EMBEDDINGSPATH/*500-dim.10-win.cbow.bin

# find correct vectors file
VECTORFILE=$($PYSCRIPTROOT/readparamspickle.py $MODELPATH/params.pickle  external_embedding | gawk -F / '{print $NF}')
if [ "$VECTORFILE" != "None" ]; then
	EXVECTORS=$EMBEDDINGSPATH/$VECTORFILE
fi

BARCHYBRID=$(ls -1 $MODELPATH/*.model_??? | tail -1)


# predict
echo "Predicting ... language: $LANGUE, start: $NOW"
#echo "Predicting ... language: $LANGUE, start: $NOW" 1>&2
#predict $CLEANTEST $MODELPATH/*.model_??? $MODELPATH/params.pickle $ALLWORDS $WORDLIST $EXVECTORS
predict $CLEANTEST $BARCHYBRID $MODELPATH/params.pickle $ALLWORDS $WORDLIST $EXVECTORS

# copy result in output folder
#cp $TMPDIR/result-deproj-reinsert.conllu $OUTPATH/$LANGUE.output.conllu
cp $TMPDIR/result-deproj-reinsert.conllu $OUTFILE

# evaulation for testing
#$PYSCRIPTROOT/evaluation_script/conll17_ud_eval.py --weights $PYSCRIPTROOT/evaluation_script/weights.clas $TEST $TMPDIR/result-deproj-reinsert.conllu

# clean up
#rm -rf $TMPDIR

