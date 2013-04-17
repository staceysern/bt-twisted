"""
The Acceptor passively waits for connection requests and accepts them.
An Acceptor is created with an address on which to accept connections and a
reference to a server to notify about new connections.  The Acceptor creates a
socket, binds it to the address and begins to listen on the socket.  It
registers with the Reactor to be notified for read events on the socket which
signal connection requests.

A server must implement the function accepted_connection().
"""

import logging
import socket
from reactor import Reactor

logger = logging.getLogger('bt.acceptor')


class Acceptor(object):
    def __init__(self, addr, server):
        self._server = server

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setblocking(0)

        self._socket.bind(addr)
        self._socket.listen(5)

        Reactor().register_for_read_events(self)

    def stream(self):
        return self._socket

    def read_event(self):
        connection, addr = self._socket.accept()
        logger.info("Accepted connection from {0}".format(str(addr)))

        self._server.accepted_connection(addr, connection)
