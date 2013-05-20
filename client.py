"""
The BitTorrentClient sets up necessary objects before starting the Twisted
reactor.  From there all other functions of the BitTorrent client are event
driven and flow from calls from the Reactor.

Initially, the client chooses a peer_id, creates an Acceptor for incoming
connections (not implemented) and creates a control channel.  It sets up
delayed calls to start serving the torrents specified on the command line
and then starts the reactor.
"""

import logging
import logging.config
import sys
import time

from ampcontrolserver import AMPControlServerFactory
from commands import MsgError
from httpcontrolserver import HTTPControlServer
from torrentmgr import TorrentMgr
from torrentmgr import TorrentMgrError

from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('bt')

_AMP_CONTROL_PORT = 1060


class BitTorrentClient(object):
    def __init__(self, reactor, filenames):
        self._reactor = reactor

        self._peer_id = "-HS0001-"+str(int(time.time())).zfill(12)
        self._torrents = {}

        # Send a placeholder for now until the Acceptor is available
        self._port = 6881

        # Set up an amp control channel
        d = (TCP4ServerEndpoint(reactor, _AMP_CONTROL_PORT, 5, 'localhost')
             .listen(AMPControlServerFactory(self)))

        @d.addErrback
        def cannotListen(failure):
            # Schedule a clean program exit for after the reactor is running
            self._reactor.callLater(.01, self.quit)
            logger.critical("Cannot listen on control port localhost:{}"
                            .format(_AMP_CONTROL_PORT))

        # Schedule any torrents named on the command line to be added after
        # the reactor is running
        for filename in sys.argv[1:]:
            self._reactor.callLater(.01, self.add_torrent, (filename))

        # The following call starts the reactor
        HTTPControlServer(self).app.run('localhost', 8080)

    # Control channel functions

    def get_torrents(self):
        """
        Returns a dictionary of information about torrents the client is
        handling keyed by the info hash.
        """
        return {info_hash: {'name': self._torrents[info_hash].name(),
                            'percent': self.get_status(info_hash)}
                for info_hash in self._torrents}

    def add_torrent(self, filename):
        """
        Attempts to start handling the torrent represented by the supplied
        metainfo file.  Raises a MsgError exception for any error condition.
        Otherwise, returns the info hash and name of the torrent.
        """
        try:
            torrent = TorrentMgr(filename, self._port, self._peer_id,
                                 self._reactor)
        except TorrentMgrError as err:
            logger.debug(err.message)
            raise MsgError(err.message)

        info_hash = torrent.info_hash().encode('hex')
        if info_hash in self._torrents:
            logger.debug("Already serving {} (key: {})"
                         .format(filename, info_hash))
            raise MsgError("Already serving {} (key: {})"
                           .format(filename, info_hash))

        torrent.start()

        self._torrents[info_hash] = torrent
        return info_hash, torrent.name()

    def get_status(self, key):
        """
        Returns status information about the torrent with the info hash equal
        to the specified key.  Raises a MsgError exception if the key is
        invalid.  Currently, the only information returned about the torrent is
        the percent downloaded.
        """
        if key in self._torrents:
            status = "{0:1.4f}".format(self._torrents[key].percent())
        else:
            logger.debug("Invalid key: {}".format(key))
            raise MsgError("Invalid key: {}".format(key))
        return status

    def quit(self):
        """
        Stop the client by shutting down the reactor.
        """
        logger.info("Quitting BitTorrent Client")
        self._reactor.stop()

if __name__ == '__main__':
    logger.info("Starting BitTorrent Client")

    BitTorrentClient(reactor, sys.argv)
