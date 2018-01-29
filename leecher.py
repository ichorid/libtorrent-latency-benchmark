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

def SetLatencies(latency):
    # Adding latency to the network device
    if latency == 0:
        os.system('sudo tc qdisc add dev ' + networkDevice + ' root netem delay ' + str(latency) + 'ms')
    else:
        os.system('sudo tc qdisc add dev ' + networkDevice + ' root netem delay ' + str(latency) + 'ms ' + str(int(round(latency / 2))) + 'ms distribution normal')

def ClearLatencies(self):
    # Remove latency settings and the (partially) downloaded torrent.
    os.system('sudo tc qdisc del dev ' + networkDevice + ' root netem')
    os.system('rm ' + downloadFolder + fileName)

def WriteSpeedsToCSV(self, speeds):
    # Write the speeds array to a .csv file
    with open(resultFolder + resultName, 'w') as f:
        for row in speeds:
            for number in row[:-1]:
                f.write(str(number))
                f.write(",")
            f.write(str(row[-1]))
            f.write("\n")





class LeechSpeedTest:
    def readEnvArgs():
        self._downloadFolder = '/mnt/seeder/'
        self._torrentFolder = '/mnt/seeder/'
        self._resultFolder = '/mnt/seeder/'
        self._torrentName = 'test.torrent'
        self._fileName = "test.file"
        self._networkDevice = 'eth0'
        # Creation of variables used within the object
        self._resultName = sys.argv[6]

    def readRunArgs():
        self._measureEvery = .1
        self._totalTime = int(sys.argv[3])
        self._iterations = round(_totalTime / _measureEvery)
        self._startIP = int(sys.argv[1])
        self._numIPs = int(sys.argv[2])

    def checkNumArgs(self):
        # Give the starting IP and the number of IPs
        self._numVars = 6
        if len(sys.argv) != _numVars + 1:
            print("This script requires arguments, the starting IP, the number of IPs, testduration, latencyintervalsize, amount of repetitions and name of result file .")

    def Leech(self):
        print('\nNow testing with latency', latency, '...')

        # Open the torrent and start downloading
        torrent = open(_torrentFolder + _torrentName, 'rb')
        ses = lt.session()
        ses.listen_on(6881, 6891)

        e = lt.bdecode(_torrent.read())
        info = lt.torrent_info(e)

        params = { 'save_path': _downloadFolder, 'storage_mode': lt.storage_mode_t.storage_mode_sparse, 'ti': info }
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
        for ipAddress in range(_startIP, (_startIP + _numIPs + 1)):
            h.connect_peer(('10.0.3.' + str(ipAddress), 6881), 0x01)

        # Save data for the amount of iterations into speed
        for i in range(_iterations):
            sys.stdout.write('\r%.1f%%' % (100 * i / _iterations))
            s = h.status()
            #state_str = ['queued', 'checking', 'downloading metadata', 'downloading', 'finished', 'seeding', 'allocating']
            speeds[i] = s.download_rate / 1000
            time.sleep(_measureEvery)
            if s.is_seeding:
                break
        sys.stdout.write('\n')

    def MeasureDownloadSpeed(latency):
        SetLatencies(latency)
        speed = Leech()
        ClearLatencies()
        return speed

    def __init__(self):
        checkNumArgs()
        readEnvArgs()
        readRunArgs()


numIntervals = int(sys.argv[5])
latencyInterval = int(sys.argv[4])
# Creation of both the latencies to be used and the save array for the speeds
latencies = [latencyInterval * x for x in range(numIntervals)]
speeds = [[0 for x in range(iterations)] for y in latencies]

# Run the tests
t = LeechSpeedTest()
for index, latency in enumerate(latencies):
    speed[index] = t.MeasureDownloadSpeed(latency)

WriteSpeedsToCSV(speeds)
