#!/bin/bash

# Note: Mininet must be run as root.  So invoke this shell script
# using sudo.

bw=15           # In Mb/s.
delay=30        # In ms
flows=500       # Number of flows to run

mn -c
pushd ~/cs244_pcc/
mkdir -p tmp
for cong in pcc cubic; do
    for lambda in `seq 1 18`; do
        dir="fct_${cong}_${lambda}"
        rm -rf tmp/$dir
        mkdir -p tmp/$dir
        python topo/pcc-file-transfer.py --bw $bw \
                                         --delay $delay \
                                         --lmbd $lambda \
                                         --flows $flows \
                                         --cong ${cong} \
                                         --dir $dir
        mn -c
        killall recvfile
        killall bwm-ng
        killall iperf
        killall server

        if [ $cong == "pcc" ]; then
            cat tmp/${dir}/sendfile_*.out | grep duration | awk '{print $2}' | sort -h > tmp/${dir}/durations
        else
            cat tmp/${dir}/recvfile.out | grep lasted | awk '{print $5}' | sort -h > tmp/${dir}/durations
        fi
        grep eth0 tmp/${dir}/link_stats > tmp/${dir}/link_util.csv
    done;
done;
python topo/plot-completion.py
