#!/bin/bash
export PYTHONPATH=$PYTHONPATH:/home/pkhorsand/local/cplex/lib/python
source P.sh
source SIM.sh
source KSIZE.sh
cd /share/hormozdiarilab/Codes/NebulousSerendipity
source venv2/bin/activate
cd src/python
source BED.sh
echo $@
python -m kmer.gapped --job $JOB --bed /share/hormozdiarilab/Codes/NebulousSerendipity/data/$BED --threads 48 --ksize $KSZ $SIM --gap 5 --fastq "$P/../Simulation/test.fq" "$@"
