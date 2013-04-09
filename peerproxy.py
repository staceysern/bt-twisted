"""
The PeerProxy represents a BitTorrent peer and communicates with and maintains 
state associated with that peer.  A PeerProxy can be created in one of two ways 
which reflect whether it or the remote end is initiating the connection.  When 
no socket is supplied, the PeerProxy is expected to initiate the connection and 
handshake with the peer.  When a socket is supplied, the far end has already 
initiated the connection and the PeerProxy should wait for a handshake from the 
far end.

The PeerProxy maintains the state of the connection through six states.
When the far end initiates a connection, the PeerProxy starts off in the
Awaiting_Handshake state.  Upon receiving a handshake, it moves to the
Bitfield_Allowed state.  When the PeerProxy initiates the connection, it starts
off in Awaiting_Connection state.  When it receives notification that a
connection has been made, it sends a handshake and moves into
Handshake_Initiated state.  Upon receiving a handshake back, it moves into
Bitfield_Allowed.  Bitfield_Allowed is the only state in which a bitfield
message may be received.  When any message is received in Bitfield_Allowed,
the state is changed to Peer_to_Peer.  When a bitfield message is received in
any state other than Bitfield_Allowed, the connection is dropped and the state
is changed to Disconnected.

The PeerProxy uses a translator to interpret the incoming stream of bytes into 
higher level messages and to construct outgoing messages into a stream of
bytes.  Initially, the PeerProxy uses a HandshakeTranslator to translate the
"handshake" protocol.  After the handshake has been established, it sets up a
PeerWireTranslator to translate the peer wire protocol.

Currently, the PeerProxy does not handle or generate keep alives at all.
"""

import logging
from connector import Connector
from handshaketranslator import HandshakeTranslator
from peerwiretranslator import PeerWireTranslator
from socketreaderwriter import SocketReaderWriter

logger = logging.getLogger('bt.peerproxy')

class PeerProxy(object):
    class _States(object):
        (Awaiting_Handshake, Awaiting_Connection, Handshake_Initiated, 
         Bitfield_Allowed, Peer_to_Peer, Disconnected) = range(6)

    def __init__(self, client, peer_id, addr, socket=None, info_hash=None):
        self._client = client
        self._socket = socket
        self._info_hash = info_hash
        self._peer_id = peer_id
        self._addr = addr

        self._choked = True;
        self._interested = False;
        self._peer_choked = True;
        self._peer_interested = False;

        if len(peer_id) != 20:
            raise ValueError("Peer id must be 20 bytes long")

        if socket == None:
            if info_hash == None or len(info_hash) != 20:
                raise ValueError("Info hash must be a 20 byte value")

            self._translator = None
            self._socketreaderwriter = None
            Connector(addr, self)        

            self._state = self._States.Awaiting_Connection
        else:
            self._setup_handshake_translator(self)
            self._state = self._States.Awaiting_Handshake

    def _setup_handshake_translator(self):
        self._socketreaderwriter = SocketReaderWriter(self._socket)

        self._translator = HandshakeTranslator()
        self._translator.set_readerwriter(self._socketreaderwriter)
        self._translator.set_receiver(self)

    def _drop_connection(self, notify_client=True):
        if self._translator:
            self._translator.unset_receiver()
            self._translator.unset_readerwriter()
            self._translator = None

        if self._socketreaderwriter:
            self._socketreaderwriter.stop()

        if self._socket:
            self._socket.close()

        self._state = self._States.Disconnected

        if notify_client:
            self._client.peer_unconnected(self) 

    def _valid_rx_state(self):
        if self._state != self._States.Peer_to_Peer:
            if self._state == self._States.Bitfield_Allowed:
                self._state = self._States.Peer_to_Peer
            else:
                if self._state != self._States.Disconnected:
                    self._drop_connection()
                return False 
        return True

    def _valid_tx_state(self):
        if self._state != self._States.Peer_to_Peer:
            if self._state == self._States.Bitfiled_Allowed:
                self._state = self._States.Peer_to_Peer
            else:
                return False 
        return True

    def addr(self):
        return self._addr

    def is_interested(self):
        return self._interested

    def is_choked(self):
        return self._choked

    def is_peer_choked(self):
        return self._peer_choked

    def is_peer_interested(self):
        return self._peer_interested

    # Connector callbacks

    def connection_complete(self, addr, socket):
        self._socket = socket
        self._setup_handshake_translator()
        
        self._translator.tx_handshake(0, self._info_hash, self._peer_id)
        self._state = self._States.Handshake_Initiated

    def connection_failed(self, addr):
        self._client.peer_unconnected(self)

    # Translator callbacks

    def connection_lost(self):
        self._drop_connection()

    # HandshakeTranslator callbacks

    def rx_handshake(self, reserved, info_hash, peer_id):
        if self._state == self._States.Handshake_Initiated:
            if info_hash != self._info_hash: 
                self._drop_connection()
            else:
                self._translator.unset_receiver()
                self._translator.unset_readerwriter()

                self._translator = PeerWireTranslator()
                self._translator.set_readerwriter(self._socketreaderwriter)
                self._translator.set_receiver(self)
                self._state = self._States.Bitfield_Allowed 

                self._translator.tx_bitfield(self._client.get_bitfield())

    def rx_non_handshake(self):
        self._drop_connection()

    # PeerWireTranslator callbacks

    def rx_bitfield(self, bitfield):
        if self._state == self._States.Bitfield_Allowed:
            self._state = self._States.Peer_to_Peer
            self._client.peer_bitfield(self, bitfield)
        else:
            self._drop_connection()

    def rx_keep_alive(self):
        pass

    def rx_choke(self):
        if self._valid_rx_state():
            self._peer_choked = True
            self._client.peer_choked(self)

    def rx_unchoke(self):
        if self._valid_rx_state():
            self._peer_choked = False
            self._client.peer_unchoked(self)

    def rx_interested(self):
        if self._valid_rx_state():
            self._peer_interested = True
            self._client.peer_interested(self)

    def rx_not_interested(self):
        if self._valid_rx_state():
            self._peer_interested = False
            self._client.peer_not_interested(self)

    def rx_have(self, index):
        if self._valid_rx_state():
            self._client.peer_has(self, index)

    def rx_request(self, index, begin, length):
        if self._valid_rx_state():
            self._client.peer_requests(self, index, begin, length)

    def rx_piece(self, index, begin, buf):
        if self._valid_rx_state():
            self._client.peer_sent_block(self, index, begin, buf)

    def rx_cancel(self, index, begin, length):
        if self._valid_rx_state():
            self._client.peer_canceled(self, index, begin, length)

    # Client calls

    def drop_connection(self):
        self._drop_connection(FALSE)

    def choke(self):
        if self._valid_tx_state():
            self._choked = True
            self._translator.tx_choke()

    def unchoke(self):
        if self._valid_tx_state():
            self._choked = False
            self._translator.tx_unchoke()

    def interested(self):
        if self._valid_tx_state():
            self._interested = True
            self._translator.tx_interested()

    def not_interested(self):
        if self._valid_tx_state():
            self._interested = False
            self._translator.tx_not_interested()

    def have(self, index):
        if self._valid_tx_state():
            self._translator.tx_have(index)

    def request(self, index, begin, length):
        if self._valid_tx_state():
            self._translator.tx_request(index, begin, length)

    def piece(self, index, begin, buf, offset):
        if self._valid_tx_state():
            self._translator.tx_piece(index, begin, buf, offset)

    def cancel(self, index, begin, length):
        if self._valid_tx_state():
            self._translator.tx_cancel(index, begin, length)


