#!/bin/bash
# this is a simple script to make xgboost in MAC nad Linux
# basically, it first try to make with OpenMP, if fails, disable OpenMP and make again
# This will automatically make xgboost for MAC users who do not have openmp support
# In most cases, type make will give what you want

# download rabit
if [ ! -d rabit ]; then
    git clone https://github.com/tqchen/rabit.git
else
    cd rabit; git pull; cd ..
fi
if make; then
    echo "Successfully build multi-thread xgboost"
else
    echo "-----------------------------"
    echo "Building multi-thread xgboost failed"
    echo "Start to build single-thread xgboost"
    make clean
    make no_omp=1
    echo "Successfully build single-thread xgboost"
fi
