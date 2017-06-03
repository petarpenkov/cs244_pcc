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
import random
import signal

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

parser.add_argument('--flows',
                    type=int,
                    help="Bandwidth of link from sender to receiver (Mb/s)",
                    required=True)

parser.add_argument('--cong',
                    help="Congestion control algorithm to use. pcc/cubic/reno",
                    default="pcc")

parser.add_argument('--lmbd-dist',
                    type=float,
                    help="Bandwidth of link from sender to receiver (Mb/s)",
                    required=True)

parser.add_argument('--time',
                    type=int,
                    help="How long to run the two flows together(s)",
                    default=1)

parser.add_argument('--dir',
                    help="Subdirectory of tmp to store results in",
                    required=True)

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
        self.addLink(sender, receiver, bw=args.bw,\
                     delay='%dms' % args.delay, max_queue_size=qsize, use_htb=True)

        return

def link_monitor(net, interval_sec=0.1):
    """Uses bwm-ng tool to collect iface tx rate stats.  Very reliable."""

    cmd = ("bwm-ng -t %s -o csv "
           "-u bytes -T rate -C ',' > %s" %
           (interval_sec * 1000, "tmp/"+args.dir+"/link_stats"))

    receiver = net.get('receiver')

    return receiver.popen(cmd, shell=True, preexec_fn=os.setsid)

def start_receiver(net):
    proc = None
    receiver = net.get('receiver')

    if args.cong == 'pcc':
        cmd = "./pcc/receiver/app/recvfile > ./tmp/%s/recvfile.out 2> ./tmp/%s/recvfile.err" % (args.dir, args.dir)
        my_env = os.environ.copy()
        my_env["LD_LIBRARY_PATH"] = "./pcc/receiver/src/"
        proc = receiver.popen(cmd, shell=True, env=my_env, preexec_fn=os.setsid)
        print "started %s" % cmd
    else:
        print "Starting iperf server..."
        # Start the iperf server ensuring it is not receiver-window limited
        #cmd = "iperf -s -w 16m > ./tmp/%s/recvfile.out 2> ./tmp/%s/recvfile.err" %(args.dir, args.dir)
        cmd = "./server > ./tmp/%s/recvfile.out 2> ./tmp/%s/recvfile.err" %(args.dir, args.dir)
        print "about to start cmd: %s" % cmd
        proc = receiver.popen(cmd, shell=True, preexec_fn=os.setsid)

    sleep(1)
    return proc

def start_sender(net, sender_id):
    receiver = net.get('receiver')
    sender = net.get('sender')

    proc = None
    if args.cong == 'pcc':
        cmd = "time -f '%%e' --output=./tmp/%s/sendfile_time_%s.out ./pcc/sender/app/sendfile %s 9000 data/100kb > ./tmp/%s/sendfile_%s.out 2> ./tmp/%s/sendfile_%s.err" %\
                (args.dir, sender_id, receiver.IP(), args.dir, sender_id, args.dir, sender_id)
        #cmd = "time -f '%%e' --output=./tmp/%s/sendfile_time_%s.out ./pcc/sender/app/sendfile %s 9000 data/100kb" %\
        #        (args.dir, sender_id, receiver.IP())
        my_env = os.environ.copy()
        my_env["LD_LIBRARY_PATH"] = "./pcc/sender/src/"
        proc = sender.popen(cmd, shell=True, env=my_env)
        print "started %s" % cmd
    else:
        #cmd = "time -f '%%e' --output=./tmp/%s/sendfile_time_%s.out iperf -n 100K -c %s > ./tmp/%s/sendfile_%s.out 2> ./tmp/%s/sendfile_%s.err" %\
        #    (args.dir, sender_id, receiver.IP(), args.dir, sender_id, args.dir, sender_id)
        cmd = "time -f '%%e' --output=./tmp/%s/sendfile_time_%s.out ./client %s:9000 < data/100kb > ./tmp/%s/sendfile_%s.out 2> ./tmp/%s/sendfile_%s.err" %\
                (args.dir, sender_id, receiver.IP(), args.dir, sender_id, args.dir, sender_id)
        print "about to start cmd: %s" % cmd
        proc = sender.popen(cmd, shell=True)
    return proc

def start_experiment(net):
    # Run PCC experiment
    monitor = link_monitor(net)
    recv = start_receiver(net)
    wait_group = []

    receiver = net.get('receiver')
    sender = net.get('sender')

    if args.cong != 'pcc':
        ip_route = sender.cmd('ip route show')
        sender.cmd('ip route change %s initcwnd %d initrwnd %d mtu 1500'
            % (ip_route.strip(), 1, 1))

        ip_route = receiver.cmd('ip route show')
        receiver.cmd('ip route change %s initcwnd %d initrwnd %d mtu 1500'
            % (ip_route.strip(), 1, 1))

    for i in range(0, args.flows):
        send_wait = start_sender(net, str(i))
        wait_group.append(send_wait)
        sleep(random.expovariate(args.lmbd_dist))

    for w in wait_group:
        w.wait()

    os.killpg(os.getpgid(monitor.pid), signal.SIGKILL)
    os.killpg(os.getpgid(recv.pid), signal.SIGKILL)

def pcc_rtt():
    # Will likely be needed TODO
    #if not os.path.exists(args.dir):
    #    os.makedirs(args.dir)
    
    topo = PCCTopo()
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()
    dumpNodeConnections(net.hosts)

    if args.cong != 'pcc':
        os.system("sysctl -w net.ipv4.tcp_congestion_control=%s" % args.cong)

    start_experiment(net)

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
