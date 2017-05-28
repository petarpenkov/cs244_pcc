#!/bin/bash

# Note: Mininet must be run as root.  So invoke this shell script
# using sudo.

bw=15           # In Mb/s.
delay=30        # In ms

mn -c
pushd ~/cs244_pcc/
mkdir -p tmp
python topo/pcc-file-transfer.py --bw $bw --delay $delay --cong pcc 
mn -c

