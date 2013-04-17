"""
The HandshakeTranslator translates a stream of bytes into higher level messages
and vice versa related to the handshake between BitTorrent peers.  The bytes
are exchanged with a readerwriter and the higher level messages are exchanged
with a receiver.  The creator of the HandshakeTranslator must subsequently
provide it with a readerwriter using the set_readerwriter() method.  When it
no longer needs the HandshakeTranslator, it should call the
unset_readerwriter() method so that all references to the HandshakeTranslator
can be released and it can be properly garbage collected.

On the receiver side, when told to transmit a handshake message, the
HandshakeTranslator generates a set of bytes to send to the readerwriter.  When
the readerwriter presents the HandshakeTranslator with a set of bytes that
represent a handshake message, the translator notifies the receiver.  It also
notifies the receiver when a non-handshake message is received or the
connection is lost.

A receiver must implement three methods, rx_handshake(), rx_non_handshake and
connection_lost().

On the readerwriter side, when incoming bytes are available, the readerwriter
asks the HandshakeTranslator for a buffer to put them into and after it has
done that, it notifies the translator that bytes have been received.  This
scheme allows the HandshakeTranslator to get enough bytes to translate the
next part of the message expected.

A readerwriter must implement set_receiver(), unset_receiver() and tx_bytes()

Right now, the HandshakeTranslor reports the handshake after it has received
the peer_id but documentation seems to indicate it should do this right after
receiving the info_hash.

Would it make sense to make a Translator base class with common code which all
the actual translators would inherit from?
"""

import logging
import struct

logger = logging.getLogger('bt.handshaketranslator')

_BUFFER_SIZE = 48
_LENGTH_LEN = 1
_REST_LEN = 48


class HandshakeTranslator(object):
    class _States(object):
        Length, Protocol, Rest = range(3)

    def __init__(self):
        self._buffer = bytearray(_BUFFER_SIZE)
        self._view = memoryview(self._buffer)

        self._rx_state = self._States.Length
        self._bytes_needed = _LENGTH_LEN
        self._bytes_received = 0

        self._receiver = None
        self._readerwriter = None

    def set_receiver(self, receiver):
        self._receiver = receiver

    def unset_receiver(self):
        self._receiver = None

    def set_readerwriter(self, readerwriter):
        self._readerwriter = readerwriter
        self._readerwriter.set_receiver(self)

    def unset_readerwriter(self):
        self._readerwriter.unset_receiver()
        self._readerwriter = None

    def get_rx_buffer(self):
        return self._view[self._bytes_received:], self._bytes_needed

    def rx_bytes(self, n):
        self._bytes_received += n
        self._bytes_needed -= n

        if self._bytes_needed == 0:
            if self._rx_state == self._States.Length:
                (length,) = struct.unpack('B',
                                          buffer(self._buffer[0:_LENGTH_LEN]))

                self._rx_state = self._States.Protocol
                self._bytes_needed = length
                self._bytes_received = 0
            elif self._rx_state == self._States.Protocol:
                buf = buffer(self._buffer[0:self._bytes_received])
                (pstr,) = struct.unpack('{}s'.format(self._bytes_received),
                                        buf)
                if pstr == 'BitTorrent protocol':
                    self._rx_state = self._States.Rest
                    self._bytes_needed = _REST_LEN
                    self._bytes_received = 0
                else:
                    if self._receiver:
                        self._receiver.rx_non_handshake()
            else:
                buf = buffer(self._buffer[0:_REST_LEN])
                (reserved, info_hash, peer_id) = struct.unpack('8s20s20s', buf)
                if self._receiver:
                    self._receiver.rx_handshake(reserved, info_hash, peer_id)

                self._rx_state = self._States.Length
                self._bytes_needed = _LENGTH_LEN
                self._bytes_received = 0

    def connection_lost(self):
        if self._receiver:
            self._receiver.connection_lost()

    def tx_handshake(self, reserved, info_hash, peer_id):
        if self._readerwriter:
            bp = list('BitTorrent protocol')
            self._readerwriter.tx_bytes(struct.pack('B19c', 19, *bp))
            self._readerwriter.tx_bytes(struct.pack('8B', *([0]*8)))
            self._readerwriter.tx_bytes(info_hash)
            self._readerwriter.tx_bytes(peer_id)
