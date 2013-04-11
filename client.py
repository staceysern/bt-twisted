"""
The BitTorrentClient sets up necessary objects before creating a Reactor and 
calling run on it to start the event loop.  From there all other functions of 
the BitTorrent client are event driven and flow from calls from the Reactor.

Initially, the client chooses a peer_id, creates an Acceptor for incoming 
connections, and creates a UserInput to get input from the user.  When
UserInput notifies that client that the user has specified that a torrent
should be served, the BitTorrentClient creates a TorrentMgr for that torrent.

Since uploading is not yet fully supported, the place of the Acceptor in the
system hasn't fully been thought out.  When the Acceptor presents an incoming
connection, a PeerProxy must be created with the connection and it should
handshake with the peer.  After the handshake, it can be determined which 
torrent the peer wishes to upload and the PeerProxy can be added to the
appropriate torrent.  It's not clear whether this functionality belongs in the
BitTorrentClient or perhaps in an incoming connection manager.

Right now, nothing handles cleanup on program exit.  Files should be flushed
and closed and sockets should be closed ideally.
"""

import logging
import logging.config
import sys
import time

from acceptor import Acceptor
from userinput import UserInput
from reactor import Reactor
from torrentmgr import TorrentMgr
from torrentmgr import TorrentMgrError

_PORT_FIRST = 6881
_PORT_LAST = 6889

logging.config.fileConfig('logging.conf') 
logger = logging.getLogger('bt')

class BitTorrentClient(object):
    def __init__(self):
        self._reactor = Reactor()

        self._peer_id = "-HS0001-"+str(int(time.time())).zfill(12)
        self._torrents = {}

        for self._port in range(_PORT_FIRST, _PORT_LAST+1):
            try:
                self._acceptor = Acceptor(("localhost", self._port), 
                                          self, self._reactor)
                break
            except Exception as err:
                logger.debug(err)
                continue
        else:
            logger.critical(("Could not find free port in range {}-{} to "+
                             "accept connections").
                             format(_PORT_FIRST, _PORT_LAST))
            sys.exit(1)

        logger.info("Listening on port {}".format(self._port))

        print ("Enter the name of one or more torrent files to serve " +
               "(one to a line).")
        UserInput(self, self._reactor)

        self._reactor.run()

    def add_torrent(self, filename):
        try:
            torrent = TorrentMgr(filename, self._port, self._peer_id,
                                 self._reactor)
        except TorrentMgrError:
            return

        self._torrents[torrent.info_hash] = torrent

    # Acceptor callback

    def accepted_connection(self, addr, connection):
        pass

if __name__ == '__main__':
    logger.info("Starting BitTorrent Client")
    BitTorrentClient()


