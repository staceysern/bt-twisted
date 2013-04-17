"""
The PeerWireTranslator is responsible for translating a stream of bytes into
higher level messages and vice versa related to the peer wire protocol between
BitTorrent peers.  The bytes are exchanged with a readerwriter and the higher
level messages are exchanged with a receiver.  The creator of the
PeerWireTranslator must subsequently provide it with a readerwriter using the
set_readerwriter() method.  When it no longer needs the PeerWireTranslator, it
should call the unset_readerwriter() method so that all references to the
PeerWireTranslator can be released and it can be properly garbage collected.

On the receiver side, when told to transmit one of the peer wire protocol
messages, the PeerWireTranslator generates a set of bytes to send to the
readerwriter.  When the readerwriter presents the PeerWireTranslator with a set
of bytes that represent one of the peer wire protocol messages, the translator
notifies the receiver.  It also notifies the receiver when a connection is
lost.

A receiver must implement the following methods: rx_keep_alive(), rx_choke(),
rx_unchoke(), rx_interested(), rx_not_interested, rx_bitfield(), rx_have(),
rx_request(), rx_piece() and rx_cancel() and connection_lost().

On the readerwriter side, when incoming bytes are available, the readerwriter
asks the PeerWireTranslator for a buffer to put them into and after it has
done that, it notifies the translator that bytes have been received.  This
scheme allows the PeerWireTranslator to get enough bytes to translate the
next part of the message expected.  It also allows an entire block of incoming
data to be placed in one buffer even if it is received over multiple socket
reads.

A readerwriter must implement set_receiver(), unset_receiver() and tx_bytes()

Would it make sense to make a Translator base class with common code which all
the actual translators would inherit from?
"""

import logging
import struct
from bitstring import BitArray

logger = logging.getLogger('bt.bttranslator')

_LENGTH_LEN = 4

_MSG_CHOKE = 0
_MSG_UNCHOKE = 1
_MSG_INTERESTED = 2
_MSG_NOT_INTERESTED = 3
_MSG_HAVE = 4
_MSG_BITFIELD = 5
_MSG_REQUEST = 6
_MSG_PIECE = 7
_MSG_CANCEL = 8


class PeerWireTranslator(object):
    class _States(object):
        Length, Message = range(2)

    def __init__(self):
        self._length_buf = bytearray(_LENGTH_LEN)
        self._length_view = memoryview(self._length_buf)
        self._length_state_setup()

        self._receiver = None
        self._readerwriter = None

        self._rx_functions = {_MSG_CHOKE: self.rx_choke,
                              _MSG_UNCHOKE: self.rx_unchoke,
                              _MSG_INTERESTED: self.rx_interested,
                              _MSG_NOT_INTERESTED: self.rx_not_interested,
                              _MSG_HAVE: self.rx_have,
                              _MSG_BITFIELD: self.rx_bitfield,
                              _MSG_REQUEST: self.rx_request,
                              _MSG_PIECE: self.rx_piece,
                              _MSG_CANCEL: self.rx_cancel}

    def _length_state_setup(self):
        self._rx_state = self._States.Length
        self._bytes_needed = _LENGTH_LEN
        self._bytes_received = 0
        self._current_buf = self._length_buf
        self._current_view = self._length_view

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
        return self._current_view[self._bytes_received:], self._bytes_needed

    def rx_bytes(self, n):
        self._bytes_received += n
        self._bytes_needed -= n

        if self._bytes_needed == 0:
            if self._rx_state == self._States.Length:
                (length,) = struct.unpack('>i', buffer(self._length_buf))
                if length == 0:
                    self.rx_keep_alive()
                    self._length_state_setup()
                else:
                    self._rx_state = self._States.Message
                    self._bytes_needed = length
                    self._bytes_received = 0

                    self._current_buf = bytearray(length)
                    self._current_view = memoryview(self._current_buf)
            else:
                (message_id,) = struct.unpack("B",
                                              buffer(self._current_buf[0:1]))

                try:
                    self._rx_functions[message_id]()
                except KeyError:
                    logger.debug("Received message with invalid msg id: {}"
                                 .format(message_id))

                self._length_state_setup()

    def rx_keep_alive(self):
        if self._receiver:
            self._receiver.rx_keep_alive()

    def rx_choke(self):
        if self._receiver:
            self._receiver.rx_choke()

    def rx_unchoke(self):
        if self._receiver:
            self._receiver.rx_unchoke()

    def rx_interested(self):
        if self._receiver:
            self._receiver.rx_interested()

    def rx_not_interested(self):
        if self._receiver:
            self._receiver.rx_not_interested()

    def rx_have(self):
        if self._receiver:
            (index,) = struct.unpack(">I", buffer(self._current_buf[1:5]))
            self._receiver.rx_have(index)

    def rx_bitfield(self):
        if self._receiver:
            bits = BitArray(bytes=self._current_buf[1:self._bytes_received])
            self._receiver.rx_bitfield(bits)

    def rx_request(self):
        if self._receiver:
            buf = buffer(self._current_buf[1:])
            index, begin, length, = struct.unpack(">3I", buf)
            self._receiver.rx_request(index, begin, length)

    def rx_piece(self):
        if self._receiver:
            index, begin, = struct.unpack(">2I",
                                          buffer(self._current_buf[1:9]))
            self._receiver.rx_piece(index, begin,
                                    buffer(self._current_buf[9:]))

    def rx_cancel(self):
        if self._receiver:
            buf = buffer(self._current_buf[1:])
            index, begin, length, = struct.unpack(">3I", buf)
            self._receiver.rx_cancel(index, begin, length)

    def tx_keep_alive(self):
        if self._readerwriter:
            self._readerwriter.tx_bytes(struct.pack('B', 0))

    def tx_choke(self):
        if self._readerwriter:
            self._readerwriter.tx_bytes(struct.pack('>IB', 1, _MSG_CHOKE))

    def tx_unchoke(self):
        if self._readerwriter:
            self._readerwriter.tx_bytes(struct.pack('>IB', 1, _MSG_UNCHOKE))

    def tx_interested(self):
        if self._readerwriter:
            self._readerwriter.tx_bytes(struct.pack('>IB', 1, _MSG_INTERESTED))

    def tx_not_interested(self):
        if self._readerwriter:
            self._readerwriter.tx_bytes(struct.pack('>IB', 1,
                                                    _MSG_NOT_INTERESTED))

    def tx_have(self, index):
        if self._readerwriter:
            self._readerwriter.tx_bytes(struct.pack('>IBI', 5,
                                                    _MSG_HAVE, index))

    def tx_bitfield(self, bits):
        if self._readerwriter:
            bitfield = bits.tobytes()
            length = len(bitfield)
            self._readerwriter.tx_bytes(struct.pack('>IB{}s'.format(length),
                                                    1+length, _MSG_BITFIELD,
                                                    bitfield))

    def tx_request(self, index, begin, length):
        if self._readerwriter:
            self._readerwriter.tx_bytes(struct.pack('>IB3I', 13, _MSG_REQUEST,
                                                    index, begin, length))

    def tx_piece(self, index, begin, block):
        if self._readerwriter:
            length = len(block)
            self._readerwriter.tx_bytes(struct.pack('>IB2I{}s'.format(length),
                                                    9+length, _MSG_PIECE,
                                                    index, begin, block))

    def tx_cancel(self, index, begin, length):
        if self._readerwriter:
            self._readerwriter.tx_bytes(struct.pack('>IB3I', 13, _MSG_CANCEL,
                                                    index, begin, length))

    def connection_lost(self):
        if self._receiver:
            self._receiver.connection_lost()
