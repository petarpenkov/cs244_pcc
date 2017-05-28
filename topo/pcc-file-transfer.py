#!/usr/bin/python
from argparse import ArgumentParser
from mininet.topo import Topo
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from subprocess import Popen, PIPE
from time import sleep

import os

parser = ArgumentParser(description="PCC fairness")

# Heavily based on Stanford CS244 Project 1 Topology 
parser.add_argument('--delay',
                    type=int,
                    help="Delay for the link between sender and receiver",
                    required=True)

parser.add_argument('--bw', '-b',
                    type=float,
                    help="Bandwidth of link from sender to receiver (Mb/s)",
                    required=True)

parser.add_argument('--cong',
                    help="Congestion control algorithm to use. pcc/cubic/reno",
                    default="pcc")

parser.add_argument('--time',
                    type=int,
                    help="How long to run the two flows together(s)",
                    default=0)

args = parser.parse_args()

class PCCTopo(Topo):
    def build(self, n=2):
        sender = self.addHost('sender')
        receiver = self.addHost('receiver')

        # Buffer set to short RTT flow BDP 
        # Since BW is in Mb/s and RTT in ms, need to multiply by 1000
        # to normalize
        mtu = 1500
        #qsize = args.bw * args.delay * 1000 / mtu
        qsize = args.bw * args.delay * 2 * 1000 / (8 * mtu)
        print "Setting queue size to %d packets" % qsize
        # Should be divided by packet size as it is in packets TODO
        self.addLink(sender, receiver, bw=args.bw, delay='%dms'\
                     % args.delay)

        return

def start_receiver(net):
    receiver = net.get('receiver')
    cmd = "./pcc/receiver/app/recvfile > ./tmp/recvfile.out 2> ./tmp/recvfile.err"
    print "about to start cmd: %s" % cmd
    my_env = os.environ.copy()
    my_env["LD_LIBRARY_PATH"] = "./pcc/receiver/src/"
    proc = receiver.popen(cmd, shell=True, env=my_env)
    print "started %s" % cmd
    sleep(1)
    return [proc]

def start_sender(net):
    receiver = net.get('receiver')
    sender = net.get('sender')
    cmd = "./pcc/sender/app/sendfile %s 9000 data/100kb >> ./tmp/sendfile.out 2> ./tmp/sendfile.err" % receiver.IP()
    print "about to start cmd: %s" % cmd
    my_env = os.environ.copy()
    my_env["LD_LIBRARY_PATH"] = "./pcc/sender/src/"
    proc = sender.popen(cmd, shell=True, env=my_env)
    print "started %s" % cmd
    sleep(1)
    return [proc]

def pcc_rtt():
    # Will likely be needed TODO
    #if not os.path.exists(args.dir):
    #    os.makedirs(args.dir)
    
    topo = PCCTopo()
    topo.build()
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()
    dumpNodeConnections(net.hosts)

    if args.cong != "pcc":
        # Run TCP experiment
        os.system("sysctl -w net.ipv4.tcp_congestion_control=%s" % args.cong)
        start_tcp_flows(net)
    else:
        # Run PCC experiment
        recv = start_receiver(net)
        for i in range(0, 100):
            send = start_sender(net)
            send[0].wait()
        recv[0].kill()

    # run with both flows
    sleep(args.time)

    net.stop()
    #os.system("killall appclient")
    #os.system("killall appserver")
    # TODO KILL EVERYTHING
    
    # From bufferbloat, might be worth doing TODO
    # Ensure that all processes you create within Mininet are killed.
    # Sometimes they require manual killing.
    # Popen("pgrep -f webserver.py | xargs kill -9", shell=True).wait()

if __name__ == "__main__":
    pcc_rtt()
