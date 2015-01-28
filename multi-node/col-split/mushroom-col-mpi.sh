#!/bin/bash
if [[ $# -ne 1 ]]
then
    echo "Usage: nprocess"
    exit -1
fi

rm -rf train.col* *.model
k=$1

# split the lib svm file into k subfiles
python splitsvm.py ../../demo/data/agaricus.txt.train train $k

# run xgboost mpi
mpirun -n $k ../../xgboost-mpi mushroom-col.conf dsplit=col

# the model can be directly loaded by single machine xgboost solver, as usuall
../../xgboost mushroom-col.conf task=dump model_in=0002.model fmap=../../demo/data/featmap.txt name_dump=dump.nice.$k.txt

# run for one round, and continue training
mpirun -n $k ../../xgboost-mpi mushroom-col.conf dsplit=col num_round=1
mpirun -n $k ../../xgboost-mpi mushroom-col.conf dsplit=col model_in=0001.model

cat dump.nice.$k.txt