import os
import sys
import time

import logging
import logging.config

from twisted.internet.defer import inlineCallbacks, Deferred, returnValue
from twisted.internet.task import deferLater
from twisted.internet import reactor
from twisted.python import log

from Tribler.Core.SessionConfig import SessionStartupConfig
from Tribler.Core.Session import Session
from Tribler.Core.DownloadConfig import DownloadStartupConfig 
from Tribler.Core.simpledefs import UPLOAD, DOWNLOAD, DLSTATUS_SEEDING
from Tribler.Core.TorrentDef import TorrentDef
from Tribler.dispersy.util import blocking_call_on_reactor_thread

from leecher import LeechSpeedTest

class LeechLib(LeechSpeedTest):
    def Leech(self):
        self.latencies = [self.startingLatency + self.latencyInterval *
                n for n in range(self.numIntervals)]
        os.system('rm -rf .tribler')
        reactor.callWhenRunning(self.TestLantencies)
        reactor.run()
        return self.bws

    @blocking_call_on_reactor_thread
    @inlineCallbacks
    def TestLantencies(self):
        logging.basicConfig(level=logging.INFO)
        
        # Redirect twisted log to standard python logging
        observer = log.PythonLoggingObserver()
        observer.start()

        # Open the torrent and start downloading
        config = SessionStartupConfig()
        config.set_state_dir(os.path.join(os.getcwd(), '.tribler'))
        config.set_torrent_checking(False)
        config.set_multicast_local_peer_discovery(False)
        config.set_megacache(False)
        config.set_dispersy(False)
        config.set_mainline_dht(False)
        config.set_torrent_store(False)
        config.set_enable_torrent_search(False)
        config.set_enable_channel_search(False)
        config.set_torrent_collecting(False)
        config.set_libtorrent(True)
        config.set_dht_torrent_collecting(False)
        config.set_videoserver_enabled(False)
        config.set_enable_metadata(False)
        config.set_http_api_enabled(False)
        config.set_tunnel_community_enabled(False)
        config.set_creditmining_enable(False)
        config.set_enable_multichain(False)

        session = Session(config)
        yield session.start()

        self.speeds = list()
        self.bws = list()
        for index, latency in enumerate(self.latencies):
            print '\nNow testing with latency', latency, '...'
            self.SetLatencies(latency)
            yield self.LeechTwisted(session)
            self.bws.append((latency, self.speeds))
            self.ClearLatencies()
        print 'EEEEEEEEEEEEEEEE'
        df = session.shutdown()
        reactor.stop()
        #df.addCallback(lambda x: reactor.stop())


    #def ShutdownTribler(self, session):

    #@blocking_call_on_reactor_thread
    @inlineCallbacks
    def LeechTwisted(self, session):
        #os.system('rm -rf download')
        dcfg = DownloadStartupConfig()
        dcfg.set_dest_dir(os.path.join(os.getcwd(), 'download'))
        dcfg.set_hops(0)
        
        tdef = TorrentDef.load(self.torrentName)
        print "\n DL START"
        download = yield session.start_download_from_tdef(tdef, dcfg=dcfg)
            
        handle = yield download.get_handle()
        for ipAddress in range(self.startIP, (self.startIP + self.numIPs)):
            handle.connect_peer(('10.0.3.' + str(ipAddress), 6881), 0x01)

        self.speeds = []
        startTime = time.time()

        # Save data for the amount of iterations into speed
        def printSpeed(ds):
            sumDl = ds.get_total_transferred(DOWNLOAD)
            progress = ds.get_progress()
            sys.stdout.write('\r%.1f%%' % (progress*100))
            sys.stdout.flush()
            self.speeds.append((time.time()-startTime, sumDl/1000))

            if(ds.get_status() == DLSTATUS_SEEDING):
                for i in range(self.numMeasurements - len(self.speeds)):
                    self.speeds.append((time.time()-startTime, -1))
                print "\nDL COMPLETE"
                def tr(x=None):
                    d.callback(None)

                session.remove_download(ds.get_download(), True, True).addCallback(tr)
                print "\nDL COMPLETE2"
                return 0.0, False
            return 0.4, False

        d = Deferred()
        download.set_state_callback(printSpeed)
        yield d
        #returnValue(d)
