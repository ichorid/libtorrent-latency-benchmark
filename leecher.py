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
import libtorrent as lt

def SetLatencies(latency, networkDevice='eth0'):
    # Adding latency to the network device
    os.system('sudo tc qdisc add dev ' + networkDevice + ' root netem delay ' + str(latency) + 'ms')
    # Commented out to produce more predictable results
    """
    if latency == 0:
        os.system('sudo tc qdisc add dev ' + networkDevice + ' root netem delay ' + str(latency) + 'ms')
    else:
        os.system('sudo tc qdisc add dev ' + networkDevice + ' root netem delay ' + str(latency) + 'ms ' + str(int(round(latency / 2))) + 'ms distribution normal')
    """

def ClearLatencies(networkDevice='eth0'):
    # Remove latency settings and the (partially) downloaded torrent.
    os.system('sudo tc qdisc del dev ' + networkDevice + ' root netem')

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

        # Open the torrent and start downloading
        torrent = open(self.torrentFolder + self.torrentName, 'rb')
        ses = lt.session(flags=0)
        ses.enable_incoming_tcp=0
        ses.enable_outgoing_tcp=0
        ses.listen_on(6881, 6891)

        e = lt.bdecode(torrent.read())
        info = lt.torrent_info(e)

        params = {  'save_path': self.downloadFolder, 
                    'storage_mode': lt.storage_mode_t.storage_mode_sparse, 
                    'ti': info }
        h = ses.add_torrent(params)
        
        # Get the settings for the tests.
        #settings = ses.get_settings()
        ## Changing the settings - experimental #
        #settings['allow_multiple_connections_per_ip'] = True
        #settings['disable_hash_checks'] = True
        #settings['low_prio_disk'] = False
        #settings['strict_end_game_mode'] = False
        #settings['smooth_connects'] = False
        #settings['connections_limit'] = 500
        #settings['recv_socket_buffer_size'] = os_default
        #settings['send_socket_buffer_size'] = os_default 
        # Set the settings
        #ses.set_settings(settings)

        # Add the peers to the torrent
        for ipAddress in range(self.startIP, (self.startIP + self.numIPs)):
            h.connect_peer(('10.0.3.' + str(ipAddress), 6881), 0x01)

        startTime = time.time()
        # Save data for the amount of measures into speed
        speeds = []
        for i in range(self.numMeasurements):
            #sys.stdout.write('\r%.1f%%' % (100 * i / self.numMeasurements))
            s = h.status()
            sys.stdout.write('\r%.1f%%' % (s.progress*100))
            #state_str = ['queued', 'checking', 'downloading metadata', 'downloading', 'finished', 'seeding', 'allocating']
            peers = h.get_peer_info()
            sumDl = 0
            for p in peers:
                sumDl += p.total_download
            speeds.append((time.time()-startTime, sumDl/1000))
            time.sleep(self.measureEvery)
            if s.is_seeding:
                break

        for i in range(self.numMeasurements - len(speeds)):
            speeds.append((time.time()-startTime, -1))

        sys.stdout.write('\n')
        ses.remove_torrent(h)
        return speeds

    def MeasureDownloadSpeed(self):
        speed = self.Leech()
        os.system('rm ' + self.downloadFolder + self.fileName)
        return speed

    def __init__(self, args):
        self.__dict__=args
        self.measureEvery = .1
        self.numMeasurements= round(self.totalTime / self.measureEvery)

def checkNumArgs():
    # Give the starting IP and the number of IPs
    numVars = 7
    if len(sys.argv) != numVars + 1:
        print("This script requires arguments: the starting IP, the number of IPs, testduration, latencyintervalsize, amount of repetitions, name of result file, starting latency .")
        exit (1)
    else:
        return {'startIP' :         int(sys.argv[1]),
                'numIPs' :          int(sys.argv[2]),
                'totalTime' :       int(sys.argv[3])}


args = checkNumArgs()
latencyInterval = int(sys.argv[4])
numIntervals    = int(sys.argv[5])
startingLatency = int(sys.argv[7])

# Creation of both the latencies to be used and the save array for the speeds
latencies = [startingLatency + latencyInterval * n for n in range(numIntervals)]
#latencies.reverse()

bws = list()
for index, latency in enumerate(latencies):
    print('\nNow testing with latency', latency, '...')
    SetLatencies(latency)
    r = LeechSpeedTest(args).MeasureDownloadSpeed()
    bws.append((latency, r))
    ClearLatencies()

WriteSpeedsToCSV(bws, resultName=sys.argv[6])
