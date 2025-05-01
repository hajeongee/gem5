#!/bin/bash

# Usage: ./run.sh <num_pairs>

ALL_PIDS=""
num_pairs=$1
num_cores=$((num_pairs * 2 + 1))


if [ $# -lt 1 ]; then
    echo "Error: Missing arguments."
    echo "Usage: $0 <num_pairs of hosts> "
    exit 1
fi

cleanup() {
    echo "Caught Interrrupt, Cleaning up"

    for p in $ALL_PIDS ; do
        kill -KILL $p &>/dev/null
    done
    date +%s
    exit 1
}

trap "cleanup" SIGINT

echo "Starting Timestamp"
date +%s

echo "$num_pairs pairs"
echo "$num_cores cores"
mpirun -n $num_cores --allow-run-as-root sst --partitioner=sst.self --add-lib-path=./ sst/x86_example.py -- --host_pairs=$num_pairs 


echo "Ending Timestamp"
date +%s