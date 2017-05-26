#!/bin/bash

# Note: Mininet must be run as root.  So invoke this shell script
# using sudo.

time=200
bwsender=1000   # In Mb/s.
bwnet=100       # In Mb/s
shortdelay=5   # TODO
longdelay=40    # TODO
serverdelay=0  # TODO
grabduration=5  # In second. Specifies how long the long RTT flow runs alone 
runduration=50 # In seconds. Specifies how long the flows compete.

killall appclient &> /dev/null
killall appserver &> /dev/null

mn -c
pushd ~/cs244_pcc/
mkdir -p tmp
rm ./tmp/srv.* &> /dev/null
rm ./tmp/short.* &> /dev/null
rm ./tmp/long.* &> /dev/null
for longdelay in 10 20 30 40 50; do
    python topo/pccFairness.py --bw-net $bwnet --bw-sender $bwsender \
                               --short-delay $shortdelay --long-delay $longdelay \
                               --server-delay $serverdelay --grab $grabduration \
                               --time $runduration --cong cubic 

    mn -c
done;

