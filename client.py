#!/usr/bin/env python

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

        def cannotListen(failure):
            # Schedule a clean program exit for after the reactor is running
            self._reactor.callLater(.01, self.quit)
            logger.critical("Cannot listen on control port localhost:{}"
                            .format(_AMP_CONTROL_PORT))
        d.addErrback(cannotListen)

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
        torrents = {}
        for info_hash in self._torrents:
            status = self.get_status(info_hash)
            torrents[info_hash] = {'name': self._torrents[info_hash].name(),
                                   'percent': status['percent']}
        return torrents

    def add_torrent(self, filename):
        """
        Returns a deferred which eventually fires with the info_hash and the
        name of the torrent specified by the filename.  In case of failure,
        a MsgError exception is raised.
        """
        torrent = TorrentMgr(filename, self._port, self._peer_id,
                             self._reactor)

        def success(value):
            info_hash = torrent.info_hash().encode('hex')
            if info_hash in self._torrents:
                logger.debug("Already serving {} (key: {})"
                             .format(filename, info_hash))
                raise MsgError("Already serving {} (key: {})"
                               .format(filename, info_hash))

            torrent.start()

            self._torrents[info_hash] = torrent

            return info_hash, torrent.name()

        def failure(failure):
            raise MsgError(failure.value.message)

        return torrent.initialize().addCallbacks(success, failure)

    def get_status(self, info_hash):
        """
        Returns a dictionary of status items related to the torrent specified
        by the supplied info_hash.  Raises a MsgError exception if the info
        hash is invalid.
        """
        if info_hash in self._torrents:
            return {'percent': "{0:1.4f}"
                               .format(self._torrents[info_hash].percent())}
        else:
            logger.debug("Invalid key: {}".format(info_hash))
            raise MsgError("Invalid key: {}".format(info_hash))

    def quit(self):
        """
        Stop the client by shutting down the reactor.
        """
        logger.info("Quitting BitTorrent Client")
        self._reactor.stop()

if __name__ == '__main__':
    logger.info("Starting BitTorrent Client")

    BitTorrentClient(reactor, sys.argv)
