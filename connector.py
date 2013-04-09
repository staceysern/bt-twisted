"""
The Connector establishes tcp connections.  Each Connector is created with an
address to connect to and a reference to a requestor to notify about the
result of the connection establishment.  The Connector creates a 
non-blocking socket and tries to connect on it.  It registers with the Reactor 
to be notified for write events on the socket so that it can determine whether 
the connect succeeds or fails.

A requestor must implement two functions, connection_complete() and
connection_failed(). 
"""

import errno
import logging
import socket
from decorators import singleton
from reactor import Reactor

logger = logging.getLogger('bt.connector')

class Connector(object):
    def __init__(self, addr, requestor, reactor):
        logger.debug("Connect to address {}".format(addr))
        self._requestor = requestor
        self._reactor = reactor 
        self._addr = addr

        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.setblocking(0)
            self._socket.connect(addr)
        except socket.error:
            err = self._socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            if err != 0 and  err != errno.EINPROGRESS:
                self._socket.close()
                logger.debug("Connection failed: {0}\n".format(err))
                requestor.connection_failed(addr)
                return

        self._reactor.register_for_write_events(self)

    def stream(self):
        return self._socket

    def write_event(self):
        self._reactor.unregister_for_write_events(self)

        err = self._socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if err == 0:
            logger.info("Connection established with {0}". 
                        format(str(self._addr)))
            self._requestor.connection_complete(self._addr, self._socket)
        elif err != 0 and  err != errno.EINPROGRESS:
            logger.info("Connection establishment failed with {0}". 
                        format(str(self._addr)))
            self._requestor.connection_failed(self._addr)


