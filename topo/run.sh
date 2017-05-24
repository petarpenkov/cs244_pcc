#!/bin/bash

# Note: Mininet must be run as root.  So invoke this shell script
# using sudo.

time=200
bwsender=1000   # In Mb/s.
bwnet=100       # In Mb/s
shortdelay=5   # TODO
longdelay=20    # TODO
serverdelay=0  # TODO
grabduration=5  # In second. Specifies how long the long RTT flow runs alone 
runduration=500 # In seconds. Specifies how long the flows compete.

killall appclient &> /dev/null
killall appserver &> /dev/null
rm /tmp/srv.* &> /dev/null
rm /tmp/short.* &> /dev/null
rm /tmp/long.* &> /dev/null

sudo mn -c
pushd ~/cs244_pcc/
mkdir -p tmp
python topo/pccFairness.py --bw-net $bwnet --bw-sender $bwsender \
                           --short-delay $shortdelay --long-delay $longdelay \
                           --server-delay $serverdelay --grab $grabduration \
                           --time $runduration
