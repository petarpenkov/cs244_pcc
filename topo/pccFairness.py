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
parser.add_argument('--short-delay',
                    type=int,
                    help="Delay for the short-RTT flow(ms)",
                    required=True)

parser.add_argument('--long-delay',
                    type=int,
                    help="Delay for the long-RTT flow(ms)",
                    required=True)

parser.add_argument('--server-delay',
                    type=int,
                    help="Delay on the bottleneck link(ms)",
                    required=True)

parser.add_argument('--bw-net', '-B',
                    type=float,
                    help="Bandwidth of bottleneck (network) link (Mb/s)",
                    required=True)

parser.add_argument('--bw-sender', '-b',
                    type=float,
                    help="Bandwidth of link from sender to switch (Mb/s)",
                    required=True)

parser.add_argument('--cong',
                    help="Congestion control algorithm to use. pcc/cubic/reno",
                    default="pcc")

parser.add_argument('--grab',
                    type=int,
                    help="How long to allow the long RTT flow to run alone(s)",
                    default=5)

parser.add_argument('--time',
                    type=int,
                    help="How long to run the two flows together(s)",
                    default=500)

args = parser.parse_args()

class PCCTopo(Topo):
    def build(self, n=3):
        switch   = self.addSwitch('s0')
        shortRTT = self.addHost('shortRTT')
        longRTT  = self.addHost('longRTT')
        server   = self.addHost('server')

        # Buffer set to short RTT flow BDP 
        # Since BW is in Mb/s and RTT in ms, need to multiply by 1000
        # to normalize. Delay is multiplied by 2 because BDP is computed
        # with RT. Divided by 8 to convert from bits to bytes.
        mtu = 1500;
        qsize = args.bw_sender * args.short_delay * 2 * 1000 / (8 * mtu)
        print "Setting queue size to %d packets" % qsize
        # Should be divided by packet size as it is in packets TODO
        self.addLink(shortRTT, switch, bw=args.bw_sender, delay='%dms'\
                     % args.short_delay)
        self.addLink(longRTT, switch, bw=args.bw_sender, delay='%dms'\
                     % args.long_delay)
        self.addLink(server, switch, bw=args.bw_net, delay='%dms'\
                     % args.server_delay, max_queue_size=qsize, use_htb=True)
                     
        return

def redirect_output(flow, algorithm, delay):
    # Delay multiplied by 2 so filename contains RTT
    name = "./tmp/%s_%s_%d" % (flow, algorithm, delay*2)
    return " > %s.out 2> %s.err" % (name, name) 

def start_tcp_flows(net):
    server = net.get('server')
    shortRTT = net.get('shortRTT')
    longRTT = net.get('longRTT')
    print "Starting iperf server..."
    # Start the iperf server ensuring it is not receiver-window limited
    # cmd = "iperf -i 1 -s -w 16m > ./tmp/srv.out 2> ./tmp/srv.err"
    cmd = "iperf -i 1 -s -w 16m"
    cmd += redirect_output("srv", args.cong, args.long_delay)
    print "about to start cmd: %s" % cmd
    server.popen(cmd, shell=True)
    sleep(1)

    # Start the iperf client on the long RTT flow.
    # Creates a long lived TCP flow.
    cmd = "iperf -i 1 -t %d -c %s" % (args.time + args.grab, server.IP())
    cmd += redirect_output("long", args.cong, args.long_delay)
    # cmd = "iperf -i 1 -t %d -c %s > ./tmp/long.out 2> ./tmp/long.err" %\
    #       (args.time + args.grab, server.IP())
    print "about to start cmd: %s" % cmd
    proc = longRTT.popen(cmd, shell=True)

    # Let the flow grab the bandwidth
    sleep(args.grab)
    # Start the iperf client on the short RTT flow.
    # Creates a long lived TCP flow.
    #cmd = "iperf -i 1 -t %d -c %s > ./tmp/short.out 2> ./tmp/short.err" %\
    #       (args.time, server.IP())
    cmd = "iperf -i 1 -t %d -c %s" % (args.time, server.IP())
    cmd += redirect_output("short", args.cong, args.long_delay)
    print "about to start cmd: %s" % cmd
    shortRTT.popen(cmd, shell=True)

def start_server(net):
    server = net.get('server')
    cmd = "./pcc/receiver/app/appserver"
    cmd += redirect_output("srv", args.cong, args.long_delay)
    print "about to start cmd: %s" % cmd
    my_env = os.environ.copy()
    my_env["LD_LIBRARY_PATH"] = "./pcc/receiver/src/"
    proc = server.popen(cmd, shell=True, env=my_env)
    print "started %s" % cmd
    sleep(1)
    return [proc]

def start_short_flow(net):
    server = net.get('server')
    shortRTT = net.get('shortRTT')
    cmd = "./pcc/sender/app/appclient %s 9000" % server.IP()
    cmd += redirect_output("short", args.cong, args.long_delay)
    print "about to start cmd: %s" % cmd
    my_env = os.environ.copy()
    my_env["LD_LIBRARY_PATH"] = "./pcc/sender/src/"
    proc = shortRTT.popen(cmd, shell=True, env=my_env)
    print "started %s" % cmd
    sleep(1)
    return [proc]

def start_long_flow(net):
    server = net.get('server')
    longRTT = net.get('longRTT')
    cmd = "./pcc/sender/app/appclient %s 9000" % server.IP()
    cmd += redirect_output("long", args.cong, args.long_delay)
    print "about to start cmd: %s" % cmd
    my_env = os.environ.copy()
    my_env["LD_LIBRARY_PATH"] = "./pcc/sender/src/"
    proc = longRTT.popen(cmd, shell=True, env=my_env)
    print "started %s" % cmd
    sleep(1) # TODO?
    return [proc]

def pcc_fairness():
    # Will likely be needed TODO
    #if not os.path.exists(args.dir):
    #    os.makedirs(args.dir)
    
    topo = PCCTopo()
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()
    dumpNodeConnections(net.hosts)

    if args.cong != "pcc":
        # Run TCP experiment
        os.system("sysctl -w net.ipv4.tcp_congestion_control=%s" % args.cong)
        start_tcp_flows(net)
    else:
        # Run PCC experiment
        start_server(net)
        start_long_flow(net)
        sleep(args.grab)
        # allow the long flow to grab the bandwidth
        start_short_flow(net)

    # run with both flows
    sleep(args.time)

    net.stop()
    os.system("killall appclient &> /dev/null")
    os.system("killall appserver &> /dev/null")
    # TODO KILL EVERYTHING
    
    # From bufferbloat, might be worth doing TODO
    # Ensure that all processes you create within Mininet are killed.
    # Sometimes they require manual killing.
    # Popen("pgrep -f webserver.py | xargs kill -9", shell=True).wait()

if __name__ == "__main__":
    pcc_fairness()
