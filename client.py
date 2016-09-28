# Retrieved on September 23st, 2016 from http://libtorrent.org/python_binding.html
# Arvid Norberg is listed as the original author of the article.

import os
import sys
import time
import libtorrent as lt
import matplotlib.pyplot as plt

latencies = [0, 20, 50, 100, 150, 200, 500]

downloadFolder = 'downloads'
torrentFolder = 'torrents'
torrentName = 'test.torrent'
figureName = 'figure'

networkDevice = 'enp0s8'

measureEvery = .1
totalTime = 10

iterations = round(totalTime / measureEvery)
speeds = [[0 for x in range(iterations)] for y in latencies]

os.system('rm ' + downloadFolder + '/torrentTest1GB')
os.system('sudo tc qdisc del dev ' + networkDevice + ' root netem')
for index, latency in enumerate(latencies):
    torrent = open(torrentFolder + "/" + torrentName, 'rb')
    print('\nNow testing with latency', latency, '...')
    os.system('sudo tc qdisc add dev ' + networkDevice + ' root netem delay ' + str(latency) + 'ms')

    ses = lt.session()
    ses.listen_on(6881, 6891)

    e = lt.bdecode(torrent.read())
    info = lt.torrent_info(e)

    params = { 'save_path': downloadFolder, 'storage_mode': lt.storage_mode_t.storage_mode_sparse, 'ti': info }
    h = ses.add_torrent(params)
    h.connect_peer(('192.168.1.100', 6881), 0x01)

    for i in range(iterations):
        sys.stdout.write('\r%.2f%%' % (100 * i / iterations))
        s = h.status()

        state_str = ['queued', 'checking', 'downloading metadata', 'downloading', 'finished', 'seeding', 'allocating']
        speeds[index][i]
        time.sleep(measureEvery)
        if s.is_seeding:
            break

    os.system('sudo tc qdisc del dev ' + networkDevice + ' root netem')
    os.system('rm ' + downloadFolder + '/torrentTest1GB')

npSpeeds = numpy.array(speeds)
plt.plot(npSpeeds.transpose())
plt.ylabel('Download speed in kb/s')
plt.savefig(figureName)