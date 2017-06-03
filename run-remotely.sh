#!/bin/bash

# set up the VM_IP
export VM_IP=`gcloud --format="value(networkInterfaces[0].accessConfigs[0].natIP)" compute instances list -r pcc`

# will ssh into the machine, and set it up
ssh mininet@${VM_IP} -C "wget https://raw.githubusercontent.com/petarpenkov/cs244_pcc/master/setup.sh && bash setup.sh"

# will run the experiments
ssh mininet@${VM_IP} -C "screen -dm bash -c 'cd cs244_pcc; pwd; ./run-experiment.sh'"
