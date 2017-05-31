#!/usr/bin/python
from argparse import ArgumentParser
import csv

# https://stackoverflow.com/questions/2801882/generating-a-png-with-matplotlib-when-display-is-undefined
import matplotlib
# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy
import re
import subprocess

parser = ArgumentParser(description='PCC fairness')

parser.add_argument('--mode',
                    help='Include median or complete data: median/full',
                    default='median')

args = parser.parse_args()

# Reads an iperf output file and extracts the bandwidth of every measurement.
# Returns a list containing all bandwidths parsed as floats
def read_tcp_bandwidths(filename):
    bws = list()
    try:
        with open(filename, 'rb') as f:
            while f.readline().find('Bandwidth') == -1:
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

def read_run_names():
    names = subprocess.check_output('ls tmp', shell=True)
    runs = list()
    for n in names.split('\n'):
        if len(n) == 0:
            continue
        runs.append(n)
    return runs
    
def plot_all(full):
    formats = dict([
        ('cubic', 'go-'),
        ('reno' , 'bx-'),
        ('pcc'  , 'r|-')
    ])
    runs = read_run_names()
    for alg in formats.keys():
        points = list()
        mins = list()
        maxes = list()
        for rtt in range(20, 120, 20):
            measurements = list()
            for r in runs:
                shortfile = 'tmp/%s/short_%s_%d.out' % (r, alg, rtt)
                longfile = 'tmp/%s/long_%s_%d.out' % (r, alg, rtt)
                # init empty
                bwshort = list()
                bwlong = list()
                if alg != 'pcc':
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
                measurements.append(avglong / avgshort)

            if len(measurements) == 0:
                continue

            median = numpy.median(measurements) 
            maximum = numpy.amax(measurements)
            minimum = numpy.amin(measurements)

            points.append([median, rtt])
            maxes.append([maximum,rtt])
            mins.append([minimum,rtt])

        relbws = [x[0] for x in points]
        delays = [x[1] for x in points]
        line, = plt.plot(delays, relbws, formats[alg], mfc='none')
        line.set_label(alg)

        if full:
            relbws = [x[0] for x in mins]
            delays = [x[1] for x in mins]
            line, = plt.plot(delays, relbws, formats[alg]+'-', mfc='none')

            relbws = [x[0] for x in maxes]
            delays = [x[1] for x in maxes]
            line, = plt.plot(delays, relbws, formats[alg]+'-', mfc='none')

    plt.ylabel('Relative throughput of long-RTT flow')
    plt.xlabel('RTT of Long-RTT flow(ms)')
    plt.legend(loc='lower left')
    if full:
        plt.savefig('plots/fairness-full.png')
    else:
        plt.savefig('plots/fairness.png')

plot_all(args.mode=='full')


