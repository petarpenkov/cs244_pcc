#!/usr/bin/python
import csv
import numpy as np
import subprocess 

# https://stackoverflow.com/questions/2801882/generating-a-png-with-matplotlib-when-display-is-undefined
import matplotlib
# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def read_link_util(filename):
    bws = list()
    try:
        with open(filename, 'rb') as f:
            reader = csv.reader(f, delimiter=',', quoting=csv.QUOTE_NONE)
            for row in reader:
                bws.append(float(row[4])) # 4th is bytes in
    except:
        pass

    return bws

def read_duration_pcc(filename):
    dur = list()
    try:
        with open(filename, 'rb') as f:
            for row in f:
                dur.append(int(row))
    except:
        pass

    return dur 

def compute_average_util(filename):
    bws = read_link_util(filename)
    # Remove leading zeros
    while len(bws)>0 and bws[0]==0:
        bws.pop(0)

    # Remove trailing zeros
    while len(bws)>0 and bws[-1]==0:
        bws.pop()

    # 15Mbit/s = 15*10^6/8 Bytes/s (in this problem)
    maxBW = 15*1000000/8
    return np.mean(bws) / maxBW * 100 # Normalize to %

def read_statistics(filename):
    dur = read_duration_pcc(filename)
    if len(dur) == 0:
        return None

    dur.sort()
    return {'mean': np.mean(dur),
            'med' : dur[len(dur)/2],
            '95th': dur[len(dur)*95/100]}

def read_duration_names():
    names = subprocess.check_output('ls tmp | grep \"fct\"', shell=True)
    dur = list()
    for n in names.split('\n'):
        if len(n) == 0:
            continue
        dur.append(n)
    return dur

def read_all_lambdas(durations):
    lambdas = list()
    for d in durations:
        l = int(d.split('_')[-1])
        if l not in lambdas:
            lambdas.append(l)

    lambdas.sort()
    return lambdas
        
def plot_all():
    formats = {
        'pcc'   : {'mean': 'k*-', 'med': 'm|-', '95th': 'go-'},
        'cubic' : {'mean': 'yo-', 'med': 'bx-', '95th': 'r^-'}
    }

    dur = read_duration_names()
    lambdas = read_all_lambdas(dur)

    for alg in formats.keys():
        means   = list()
        medians = list()
        perc95   = list()
        for lmbd in lambdas:
            stats = read_statistics('tmp/fct_%s_%d/durations' % (alg, lmbd))
            if stats == None:
                continue
            util = compute_average_util('tmp/fct_%s_%d/link_util.csv' % (alg, lmbd))
            if util > 80:
                continue

            means.append([util, stats['mean']])
            medians.append([util, stats['med']])
            perc95.append([util, stats['95th']])

        if len(means) == 0:
            continue

        means.sort(key=lambda x: x[0])
        medians.sort(key=lambda x: x[0])
        perc95.sort(key=lambda x: x[0])

        utils = [x[0] for x in means]
        fcts  = [x[1] for x in means]
        line, = plt.plot(utils, fcts, formats[alg]['mean'], mfc='none')
        line.set_label(alg.upper()+'-average')

        utils = [x[0] for x in medians]
        fcts  = [x[1] for x in medians]
        line, = plt.plot(utils, fcts, formats[alg]['med'], mfc='none')
        line.set_label(alg.upper()+'-median')

        utils = [x[0] for x in perc95]
        fcts  = [x[1] for x in perc95]
        line, = plt.plot(utils, fcts, formats[alg]['95th'], mfc='none')
        line.set_label(alg.upper()+'-95th')

    
    plt.ylabel('Flow Completion Time (ms)')
    plt.xlabel('Network Load (%)')
    plt.legend(loc='upper left')
    plt.savefig('plots/fct.png')

plot_all()
