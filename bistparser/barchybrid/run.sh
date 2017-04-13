#export LD_LIBRARY_PATH=/home/langnat/conll2017/bistparser/cnn-v1-gpu/pycnn
export LD_LIBRARY_PATH=/home/Orange-Deskin/conll2017/cnn-v1-gpu/pycnn

TESTFILE=../../data/dev.conllu

if [ "$1" != "" ]; then
	TESTFILE=$1
fi

python src/parser.py --cnn-mem 4000 --predict \
	--outfile re.conll \
	--model ../../data/fr/barchybrid.model_004 \
	--params ../../data/fr/params.pickle \
	--extrn ../../data/fr/fr.500-dim.10-win.cbow.bin \
	--extrnFilter ../../data/allwords.txt \
	--test $TESTFILE

../../py/evaluation_script/conll17_ud_eval.py --weights ../../py/evaluation_script/weights.clas $TESTFILE re.conll 