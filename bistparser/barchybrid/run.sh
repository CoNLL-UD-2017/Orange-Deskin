#export LD_LIBRARY_PATH=/home/langnat/conll2017/bistparser/cnn-v1-gpu/pycnn
export LD_LIBRARY_PATH=/home/Orange-Deskin/conll2017/cnn-v1-gpu/pycnn

MYDIR=$(dirname $0)
TESTFILE=$MYDIR/../../test/fr.dev.conllu

if [ "$1" != "" ]; then
	TESTFILE=$1
fi



echo python $MYDIR/src/parser.py --cnn-mem 4000 --predict \
	--outfile re.conll \
	--model $MYDIR/../../data/fr/barchybrid.model_006 \
	--params $MYDIR/../../data/fr/params.pickle \
	--extrn $MYDIR/../../data/fr/fr.500-dim.10-win.cbow.bin \
	--extrnFilter $MYDIR/../../data/fr/allwords.txt \
	--test $TESTFILE

$MYDIR/../../py/evaluation_script/conll17_ud_eval.py --weights $MYDIR/../../py/evaluation_script/weights.clas $TESTFILE re.conll 


