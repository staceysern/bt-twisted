"""
The BitTorrentClient sets up necessary objects before starting the Twisted
reactor.  From there all other functions of the BitTorrent client are event 
driven and flow from calls from the Reactor.

Initially, the client chooses a peer_id and creates an Acceptor for incoming 
connections (not implemented).  It sets up delayed calls to start serving the
torrents specified on the command line and then starts the reactor.
"""

import logging
import logging.config
import sys
import time

from torrentmgr import TorrentMgr
from torrentmgr import TorrentMgrError
from twisted.internet import reactor

logging.config.fileConfig('logging.conf') 
logger = logging.getLogger('bt')

class BitTorrentClient(object):
    def __init__(self, files, reactor):
        self._reactor = reactor

        self._peer_id = "-HS0001-"+str(int(time.time())).zfill(12)
        self._torrents = {}

        # Send a placeholder for now until the Acceptor is available
        self._port = 6881

        for filename in sys.argv[1:]:
            self._reactor.callLater(.01, self.add_torrent, (filename))
            
        self._reactor.run()

    def add_torrent(self, filename):
        try:
            torrent = TorrentMgr(filename, self._port, self._peer_id,
                                 self._reactor)
        except TorrentMgrError:
            return

        self._torrents[torrent.info_hash] = torrent

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print >> sys.stderr, "usage: {} filename ...\n"
        logger.critical("usage: {} filename ...")
        sys.exit(1)

    logger.info("Starting BitTorrent Client")
    
    BitTorrentClient(sys.argv, reactor)
   


