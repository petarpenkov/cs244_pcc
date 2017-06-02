#!/bin/bash

# Note: Mininet must be run as root.  So invoke this shell script
# using sudo.

bwsender=100   # In Mb/s.
bwnet=100       # In Mb/s
shortdelay=5    # 10ms RTT on the short RTT flow 
longdelay=10    # 20ms default RTT on the long RTT flow
serverdelay=0   # No delay on the bottleneck
grabduration=5  # In second. Specifies how long the long RTT flow runs alone 
runduration=500   # In seconds. Specifies how long the flows compete.

killall appclient &> /dev/null
killall appserver &> /dev/null

mn -c
pushd ~/cs244_pcc/
rm -r tmp
mkdir -p tmp

if [ "$#" -ge 2 ]; then
    echo "Usage: sudo ./run.sh #"
    exit 1
elif [ "$#" -eq 0 ]; then
    niter=1
elif [ "$1" -ge 1 ] 2>/dev/null ; then
    niter=$1
else
    echo "Argument 1 expected to be positive integer"
    exit 2
fi

for iter in `seq 1 $niter`;do
    dir="run$iter"
    mkdir -p tmp/$dir
    for algorithm in "pcc" "reno" "cubic"; do
        for longdelay in  10 20 30 40 50; do
            python topo/pccFairness.py --bw-net $bwnet --bw-sender $bwsender \
                                       --short-delay $shortdelay\
                                       --long-delay $longdelay\
                                       --server-delay $serverdelay\
                                       --grab $grabduration\
                                       --time $runduration --cong $algorithm \
                                       --dir $dir
        done;
   done;
done;

mn -c

mkdir -p plots
python topo/plotFairness.py
python topo/plotFairness.py --mode full
