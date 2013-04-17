"""
The SocketReaderWriter manages reading and writing on a socket.  On the receive
side, a SocketReaderWriter registers with the Reactor to be notified when the
socket is ready to be read.  However, it only reads from the socket when a
receiver has been set on the SocketReaderWriter.  It first asks the receiver
for a buffer in which to place the data.  Then it reads from the socket
directly into the buffer and notifies the receiver that bytes have been
received.  The SocketReaderWriter also notifies the receiver if the connection
is lost.

A receiver must implement the functions rx_bytes() and connection_lost()

On the send side, when the SocketReaderWriter is told to transmit a string of
bytes, it places them in a list of byte strings to go out.  The
SocketReaderWriter only registers to be notified that the socket is ready to
write when the output list becomes non-empty and unregisters when the output
list becomes empty again.  Each time the socket is ready for writing, the
SocketReaderWriter attempts to transmit an entire byte string and then removes
the bytes that were actually sent from the output list.
"""

import logging
import socket
from reactor import Reactor

logger = logging.getLogger('bt.socketreaderwriter')


class SocketReaderWriter(object):
    def __init__(self, sock):
        self._reactor = Reactor()
        self._receiver = None
        self._output = []
        self._socket = sock
        self._reactor.register_for_read_events(self)

    def stream(self):
        return self._socket

    def stop(self):
        self._reactor.unregister_for_read_events(self)
        self._reactor.unregister_for_write_events(self)

    def set_receiver(self, receiver):
        self._receiver = receiver

    def unset_receiver(self):
        self._receiver = None

    def read_event(self):
        if self._receiver:
            view, size = self._receiver.get_rx_buffer()

            try:
                n = self._socket.recv_into(view, size)
                if n > 0:
                    self._receiver.rx_bytes(n)
                else:
                    if self._receiver:
                        self._receiver.connection_lost()
            except socket.error as err:
                logger.info("Socket Error {}".format(err))
                self._receiver.connection_lost()

    def write_event(self):
        if self._output == []:
            self._reactor.unregister_for_write_events(self)
        else:
            while self._output != []:
                n = self._socket.send(self._output[0])

                if n == len(self._output[0]):
                    del self._output[0]
                else:
                    self._output[0] = self._output[0][n:]
                    break

    def tx_bytes(self, bytestr):
        self._output.append(bytestr)
        if len(self._output) == 1:
            self._reactor.register_for_write_events(self)
