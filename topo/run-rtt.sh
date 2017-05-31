#!/bin/bash

# Note: Mininet must be run as root.  So invoke this shell script
# using sudo.

bw=15           # In Mb/s.
delay=100        # In ms
#lambda=20       # Lambda value (1/beta) of the exponential distribution
flows=200       # Number of flows to run


for cong in pcc cubic; do
    for lambda in `seq 2 3`; do
        mn -c
        pushd ~/cs244_pcc/
        mkdir -p tmp
        python topo/pcc-file-transfer.py --bw $bw \
                                         --delay $delay \
                                         --lmbd $lambda \
                                         --flows $flows \
                                         --cong ${cong}
        mn -c
        killall recvfile
        killall bwm-ng
        killall iperf

        cat tmp/sendfile_*.out | grep duration | grep -o '[0-9]*' | sort -h > ~/out_${cong}_${lambda}
        grep eth0 tmp/link_stats > ~/eth0-link-util_${cong}_${lambda}.csv
    done;
done;
