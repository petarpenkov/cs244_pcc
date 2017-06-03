We have found that the easiest way to setup a virtual machine is
setting up the [gcloud](https://cloud.google.com/sdk/downloads) kit.
Once it is set up, you can run the following command to create a
project and a suitable instance:

    gcloud init ;
    gcloud compute images create mininet-image --source-uri=https://storage.googleapis.com/mininet/disk.tar.gz ;
    gcloud compute instances create pcc --image=mininet-image --custom-cpu=4 --custom-memory=3840MiB ;

The first line will init the gcloud kit and prompt you to create a
project. The second line will create a mininet image from our
disk.tar.gz file, while the third command will create an instance from
the mininet-image. Alternatively, one can use the web UI to create a
VM image from the URI at
[https://storage.googleapis.com/mininet/disk.tar.gz](https://storage.googleapis.com/mininet/disk.tar.gz)
and then create an instance from the image. We recommend at least 4
CPUs and the associated memory quantity.

Further, once instance exists, please run the following three commands:

    wget https://raw.githubusercontent.com/petarpenkov/cs244_pcc/master/run-remotely.sh && chmod +x run-remotely.sh && ./run-remotely.sh ;

The above will run several commands that require ssh and gcloud. 

The default password required for ssh login is ‘mininet’ (no quotes). We recommend that this is changed by the team that reproduces these results.

    export VM_IP=`gcloud --format="value(networkInterfaces[0].accessConfigs[0].natIP)" compute instances list -r pcc` ;
    ssh mininet@${VM_IP} ;

And once into the VM, execute

    screen -dr

To see the progress report, while it runs. See man screen on how to
use it.

The results will be ready in about 8 hours. Once the results are done, you can copy the
plots to your machine by executing

    scp mininet@${VM_IP}:’/home/mininet/cs244_pcc/plots/*’ .

The default password required for ssh login is ‘mininet’. We recommend
that this is changed by the team that reproduces these results.

Once the experiments are done, there will be a file named 'done' in the home folder of the VM instance. This is created by run-experiment.sh at the end.

We can provide an IP address to a machine that is already set up with
all dependencies and scripts. We have not provided that here for
security considerations. Please contact us at Hristo Stoyanov
<stoyanov (at) stanford> or Petar Penkov <ppenkov (at) stanford>.
