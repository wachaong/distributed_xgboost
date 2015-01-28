#!/bin/bash
# map feature using indicator encoding, also produce featmap.txt
#python mapfeat.py
# split train and test
#python mknfold.py agaricus.txt 1
# training and output the models
#./../xgboost mushroom.conf
#ython ../../rabit/tracker/rabit_demo.py -n 5  ../../xgboost mushroom.conf
path=/data1/saleleads_predcit/tools/experiment/xgboost
hadoop fs -rm -r /ad_model/saleleads/tmp/test/model

#python ../../rabit/tracker/rabit_hadoop.py -n 2  -f $path/demo/binary_classification/mushroom_hadoop.conf -i /ad_model/saleleads/tmp/test/agaricus.txt.train -o /ad_model/saleleads/tmp/test/model ../../xgboost mushroom_hadoop.conf  dsplit=row num_round=3 data=stdin  model_out=stdout 
#python ../../rabit/tracker/rabit_hadoop.py -n 2 -i /ad_model/saleleads/tmp/test/agaricus.txt.train -o /ad_model/saleleads/tmp/test/model -f $path/demo/binary_classification/mushroom_hadoop.conf#../../xgboost \
#    --jobname xgboost_hadoop xgboost mushroom.hadoop.conf data=stdin model_out=stdout dsplit=row
# output prediction task=pred 
#../../xgboost mushroom.conf task=pred model_in=0002.model
# print the boosters of 00002.model in dump.raw.txt
#../../xgboost mushroom.conf task=dump model_in=0002.model name_dump=dump.raw.txt 
# use the feature map in printing for better visualization
#../../xgboost mushroom.conf task=dump model_in=0002.model fmap=featmap.txt name_dump=dump.nice.txt
#cat dump.nice.txt

