#!/bin/bash

if [ "$#" -lt 3 ];
then
	echo "Usage: <num_of_slave_nodes> <nthread> <path_in_HDFS>"
	exit -1
fi
#test data path:/ad_model/saleleads/sample/20141130_1_30_V0_V0_filter20000

# put the local training file to HDFS
hadoop fs -rm -r $3/model
rm -rf ./final.model
# training and output the final model file

../../rabit/tracker/rabit_hadoop.py  -n $1 -nt $2 -i $3/train/* -o $3/model ../../xgboost saleleads.hadoop.conf  nthread=$2 dsplit=row

# get the final model file
hadoop fs -get $3/model/part-00000 ./final.model

# output prediction task=pred 
../../xgboost saleleads.hadoop.conf task=pred model_in=final.model \
test:data=/data1/saleleads_predcit/tmp/tmp/20141130_1_30_V0_V0/filter20000/20141130_1_30_V0_V0_filter20000train

# print the boosters of final.model in dump.raw.txt
# use the feature map in printing for better visualization
