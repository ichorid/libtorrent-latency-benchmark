import os
import sys
import time
import libtorrent as lt
from leecher import LeechSpeedTest
class LeechLib(LeechSpeedTest):
    def Leech(self):
        # Open the torrent and start downloading
        ses = lt.session(flags=0)
        print ses
        ses.enable_incoming_tcp=0
        ses.enable_outgoing_tcp=0
        ses.listen_on(6881, 6891)

        torrent = open(self.torrentFolder + self.torrentName, 'rb')
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
            #sys.stdout.write('\r%.1f%%' % (s.progress*100))
            sys.stdout.write('\r%.1f%%' % (s.progress*100))
            sys.stdout.flush()
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
