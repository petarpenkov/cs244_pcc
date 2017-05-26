#!/usr/bin/python
import csv

# https://stackoverflow.com/questions/2801882/generating-a-png-with-matplotlib-when-display-is-undefined
import matplotlib
# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
# Reads an iperf output file and extracts the bandwidth of every measurement.
# Returns a list containing all bandwidths parsed as floats


def read_tcp_bandwidths(filename):
    bws = list()
    try:
        with open(filename, 'rb') as f:
            while f.readline().find("Bandwidth") == -1:
                # Skip until you read the header of the iperf output table
                pass
            reader = csv.reader(f, delimiter=' ', quoting=csv.QUOTE_NONE)
            for row in reader:
                # Bandwidths value is the second to last
                bws.append(float(row[len(row)-2])) 
    except:
        pass

    return bws

def read_pcc_bandwidths(filename):
    bws = list()
    try:
        with open(filename, 'rb') as f:
            # skip the header
            f.readline()

            reader = csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE)
            for row in reader:
                # Bandwidths value is the first 
                bws.append(float(row[0])) 
    except: 
        pass

    return bws

def plot_all():
    plt.axis([20 , 100, 0 , 1.2])
    formats = dict([
        ("cubic", "go-"),
        ("reno" , "bx-"),
        ("pcc"  , "r|-")
    ])
    for alg in formats.keys():
        points = list()
        for rtt in range(20, 120, 20):
            shortfile = "tmp/short_%s_%d.out" % (alg, rtt)
            longfile = "tmp/long_%s_%d.out" % (alg, rtt)
            # init empty
            bwshort = list()
            bwlong = list()
            if alg != "pcc":
                bwshort = read_tcp_bandwidths(shortfile)
                bwlong = read_tcp_bandwidths(longfile)
            else:
                bwshort = read_pcc_bandwidths(shortfile)
                bwlong = read_pcc_bandwidths(longfile)
            shortlen = len(bwshort)
            longlen = len(bwlong)
            if shortlen * longlen == 0:
                # No data for the current data point
                continue
            avgshort = sum(bwshort) / shortlen
            avglong = sum(bwlong) / longlen
            points.append([avgshort / avglong, rtt])

        relbws = [x[0] for x in points]
        delays = [x[1] for x in points]
        line, = plt.plot(delays, relbws, formats[alg], mfc="none")
        line.set_label(alg)

    plt.ylabel('Relative throughput of long-RTT flow')
    plt.xlabel('RTT of Long-RTT flow(ms)')
    plt.legend(loc="lower left")
    plt.savefig('plots/fairness.png')
plot_all()


