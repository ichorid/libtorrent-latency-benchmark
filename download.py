import os
import sys
import time
import libtorrent as lt
import logging
import logging.config

from twisted.internet.defer import inlineCallbacks
from twisted.internet import reactor
from twisted.python import log

from Tribler.Core.SessionConfig import SessionStartupConfig
from Tribler.Core.Session import Session
from Tribler.Core.DownloadConfig import DownloadStartupConfig 
from Tribler.Core.simpledefs import UPLOAD, DOWNLOAD
from Tribler.Core.TorrentDef import TorrentDef


@inlineCallbacks
def main():
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

    dcfg = DownloadStartupConfig()
    dcfg.set_dest_dir(os.path.join(os.getcwd(), 'download'))
    dcfg.set_hops(0)
    
    tdef = TorrentDef.load('ubuntu-17.10.1-desktop-amd64.iso.torrent')
    download = yield session.start_download_from_tdef(tdef, dcfg=dcfg)
        
    handle = yield download.get_handle()
    #handle.connect_peer(('10.0.3.248', 6881), 0x01)
    
    # Save data for the amount of iterations into speed
    def printSpeed(ds):
        print ds.get_current_speed(UPLOAD), ds.get_current_speed(DOWNLOAD), ds.get_progress()
        return 1.0, False

    download.set_state_callback(printSpeed)

reactor.callWhenRunning(main)
reactor.run()
