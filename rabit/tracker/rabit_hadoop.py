#!/usr/bin/python
"""
This is a script to submit rabit job using hadoop streaming
submit the rabit process as mappers of MapReduce
"""
import argparse
import sys
import os
import time
import subprocess
import warnings
import rabit_tracker as tracker


#!!! Set path to hadoop and hadoop streaming jar here
hadoop_binary = 'hadoop'
hadoop_streaming_jar = None

# code 
hadoop_home = os.getenv('HADOOP_HOME')
if hadoop_home != None:
    if hadoop_binary == None:
        hadoop_binary = hadoop_home + '/bin/hadoop'
        assert os.path.exists(hadoop_binary), "HADDOP_HOME does not contain the hadoop binary"
    if hadoop_streaming_jar == None:
        hadoop_streaming_jar = hadoop_home + '/share/hadoop/tools/lib/hadoop-streaming-2.4.1.jar'
        assert os.path.exists(hadoop_streaming_jar), "HADDOP_HOME does not contain the haddop streaming jar"

if hadoop_binary == None or hadoop_streaming_jar == None:
    warnings.warn('Warning: Cannot auto-detect path to hadoop and hadoop-streaming jar\n'\
                      '\tneed to set them via arguments -hs and -hb\n'\
                      '\tTo enable auto-detection, you can set enviroment variable HADOOP_HOME'\
                      ', or modify rabit_hadoop.py line 14')

parser = argparse.ArgumentParser(description='Rabit script to submit rabit jobs using Hadoop Streaming.'\
                                     'This script support both Hadoop 1.0 and Yarn(MRv2), Yarn is recommended')
parser.add_argument('-n', '--nworker', required=True, type=int,
                    help = 'number of worker proccess to be launched')
parser.add_argument('-nt', '--nthread', default = -1, type=int,
                    help = 'number of thread in each mapper to be launched, set it if each rabit job is multi-threaded')
parser.add_argument('-i', '--input', required=True,
                    help = 'input path in HDFS')
parser.add_argument('-o', '--output', required=True,
                    help = 'output path in HDFS')
parser.add_argument('-v', '--verbose', default=0, choices=[0, 1], type=int,
                    help = 'print more messages into the console')
parser.add_argument('-ac', '--auto_file_cache', default=1, choices=[0, 1], type=int,
                    help = 'whether automatically cache the files in the command to hadoop localfile, this is on by default')
parser.add_argument('-f', '--files', default = [], action='append',
                    help = 'the cached file list in mapreduce,'\
                        ' the submission script will automatically cache all the files which appears in command'\
                        ' This will also cause rewritten of all the file names in the command to current path,'\
                        ' for example `../../kmeans ../kmeans.conf` will be rewritten to `./kmeans kmeans.conf`'\
                        ' because the two files are cached to running folder.'\
                        ' You may need this option to cache additional files.'\
                        ' You can also use it to manually cache files when auto_file_cache is off')
parser.add_argument('--jobname', default='auto', help = 'customize jobname in tracker')
parser.add_argument('--timeout', default=600000000, type=int,
                    help = 'timeout (in million seconds) of each mapper job, automatically set to a very long time,'\
                        'normally you do not need to set this ')
parser.add_argument('-mem', '--memory_mb', default=-1, type=int,
                    help = 'maximum memory used by the process, Guide: set it large (near mapred.cluster.max.map.memory.mb)'\
                        'if you are running multi-threading rabit,'\
                        'so that each node can occupy all the mapper slots in a machine for maximum performance')
if hadoop_binary == None:
    parser.add_argument('-hb', '--hadoop_binary', required = True,
                        help="path-to-hadoop binary folder")  
else:
    parser.add_argument('-hb', '--hadoop_binary', default = hadoop_binary, 
                        help="path-to-hadoop binary folder")  

if hadoop_streaming_jar == None:
    parser.add_argument('-hs', '--hadoop_streaming_jar', required = True,
                        help='path-to hadoop streamimg jar file')
else:
    parser.add_argument('-hs', '--hadoop_streaming_jar', default = hadoop_streaming_jar,
                        help='path-to hadoop streamimg jar file')
parser.add_argument('command', nargs='+',
                    help = 'command for rabit program')
args = parser.parse_args()

if args.jobname == 'auto':
    args.jobname = ('Rabit[nworker=%d]:' % args.nworker) + args.command[0].split('/')[-1];

# detech hadoop version
(out, err) = subprocess.Popen('%s version' % args.hadoop_binary, shell = True, stdout=subprocess.PIPE).communicate()
out = out.split('\n')[0].split()
assert out[0] == 'Hadoop', 'cannot parse hadoop version string'
hadoop_version = out[1].split('.')
use_yarn = int(hadoop_version[0]) >= 2

if not use_yarn:
    print 'Current Hadoop Version is %s' % out[1]

def hadoop_streaming(nworker, worker_args, use_yarn):
    fset = set()
    if args.auto_file_cache:
        for i in range(len(args.command)):
            f = args.command[i]
            if os.path.exists(f):
                fset.add(f)
                if i == 0:
                    args.command[i] = './' + args.command[i].split('/')[-1]                    
                else:
                    args.command[i] = args.command[i].split('/')[-1]    
    kmap = {}
    # setup keymaps
    if use_yarn:
        kmap['nworker'] = 'mapreduce.job.maps'
        kmap['jobname'] = 'mapreduce.job.name'
        kmap['nthread'] = 'mapreduce.map.cpu.vcores'
        kmap['timeout'] = 'mapreduce.task.timeout'
        kmap['memory_mb'] = 'mapreduce.map.memory.mb'
    else:
        kmap['nworker'] = 'mapred.map.tasks'
        kmap['jobname'] = 'mapred.job.name'
        kmap['nthread'] = None
        kmap['timeout'] = 'mapred.task.timeout'
        kmap['memory_mb'] = 'mapred.job.map.memory.mb'
    cmd = '%s jar %s' % (args.hadoop_binary, args.hadoop_streaming_jar)
    cmd += ' -D%s=%d' % (kmap['nworker'], nworker)
    cmd += ' -D%s=%s' % (kmap['jobname'], args.jobname)
    if args.nthread != -1:
        if kmap['nthread'] is None:
            warnings.warn('nthread can only be set in Yarn(Hadoop version greater than 2.0),'\
                              'it is recommended to use Yarn to submit rabit jobs')
        else:
            cmd += ' -D%s=%d' % (kmap['nthread'], args.nthread)
    cmd += ' -D%s=%d' % (kmap['timeout'], args.timeout)
    if args.memory_mb != -1:
        cmd += ' -D%s=%d' % (kmap['timeout'], args.timeout)

    cmd += ' -input %s -output %s' % (args.input, args.output)
    cmd += ' -mapper \"%s\" -reducer \"/bin/cat\" ' % (' '.join(args.command + worker_args))
    if args.files != None:
        for flst in args.files:
            for f in flst.split('#'):
                fset.add(f)
    for f in fset:
        cmd += ' -file %s' % f
    print cmd
    subprocess.check_call(cmd, shell = True)

fun_submit = lambda nworker, worker_args: hadoop_streaming(nworker, worker_args, int(hadoop_version[0]) >= 2)
tracker.submit(args.nworker, [], fun_submit = fun_submit, verbose = args.verbose)
