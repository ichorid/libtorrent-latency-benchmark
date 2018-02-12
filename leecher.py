#!/usr/bin/env python3
# leecher.py

"""
This script tests the downloading speed from the given IPS of different latencies.
This is done by netem to emulate the latency.
The results are then saved to a .csv file
"""

import os
import sys
import time


def WriteSpeedsToCSV(speeds, resultFolder = '/mnt/leecher/', resultName = 'result.csv'):
    # Write the speeds array to a .csv file
    # Format of CSV:
    # | latencyA | timestampA0 | numKbytesA0 | timestampA1 | numKbytesA1 | ...
    # | latencyB | timestampB0 | numKbytesB0 | timestampB1 | numKbytesB1 | ...
    with open(resultFolder + resultName, 'w') as f:
        for lrow in speeds:
            latency, row = lrow
            f.write(str(latency))
            for record in row:
                ts, dl = record
                f.write(",")
                f.write(str(ts)) # Timestamp
                f.write(",")
                f.write(str(dl)) # Downloaded kbytes
            f.write("\n")

class LeechSpeedTest(object):
    downloadFolder = '/mnt/leecher/'
    torrentFolder = '/mnt/leecher/'
    resultFolder = '/mnt/leecher/'
    torrentName = 'test.torrent'
    fileName = "test.file"

    def Leech(self):
        raise NotImplementedError 

    def MeasureDownloadSpeed(self):
        self.Leech()
        os.system('rm ' + self.downloadFolder + self.fileName)
        return self.bws

    def __init__(self, args):
        self.__dict__=args
        self.measureEvery = .1
        self.numMeasurements= int(round(self.totalTime / self.measureEvery))
    def SetLatencies(self, latency, networkDevice='eth0'):
        # Adding latency to the network device
        os.system('sudo tc qdisc add dev ' + networkDevice + ' root netem delay ' + str(latency) + 'ms')
        # Commented out to produce more predictable results
        """
        if latency == 0:
            os.system('sudo tc qdisc add dev ' + networkDevice + ' root netem delay ' + str(latency) + 'ms')
        else:
            os.system('sudo tc qdisc add dev ' + networkDevice + ' root netem delay ' + str(latency) + 'ms ' + str(int(round(latency / 2))) + 'ms distribution normal')
        """

    def ClearLatencies(self, networkDevice='eth0'):
        # Remove latency settings and the (partially) downloaded torrent.
        os.system('sudo tc qdisc del dev ' + networkDevice + ' root netem')

def checkNumArgs():
    # Give the starting IP and the number of IPs
    numVars = 8
    if len(sys.argv) != numVars + 1:
        print "This script requires arguments: the starting IP, the number of IPs, testduration, latencyintervalsize, amount of repetitions, name of result file, starting latency, name of library to use (tribler or libtorrent) ."
        exit (1)
    else:
        return {'startIP' :         int(sys.argv[1]),
                'numIPs' :          int(sys.argv[2]),
                'totalTime' :       int(sys.argv[3]),
                'latencyInterval' : int(sys.argv[4]),
                'numIntervals'    : int(sys.argv[5]),
                'startingLatency' : int(sys.argv[7])}


def main():
    args = checkNumArgs()
    leechLibrary = sys.argv[8]

    if leechLibrary == "tribler":
        from leechTribler import LeechLib 
    else:
        from leechLibtorrent import LeechLib 

    # Creation of both the latencies to be used and the save array for the speeds
    #latencies.reverse()

    bws = list()
    bws = LeechLib(args).MeasureDownloadSpeed()
    WriteSpeedsToCSV(bws, resultName=sys.argv[6])


if __name__=="__main__":
    main()

