"""
The ProtocolAdapterFactory creates a ProtocolAdapter for each new connection.  
For a client endpoint, a ProtocolAdapterFactory is passed on the connect call 
and its buildProtocol method is called when the connection is established.  For
a server endpoint, a ProtocolAdapterFactory is passed on the listen call 
and its buildProtocol method is called when a new connection is accepted.

On the receive side, the ProtocolAdapter interfaces with a receiver to transfer 
data delivered by the reactor.  When the reactor calls the ProtocolAdapter's 
dataReceived method, the ProtocolAdapter asks the receiver for a buffer in 
which to place the data, copies the data to the buffer and notifies the receiver
that bytes have been received.  It repeats this until all the received data 
has been passed on to the receiver.  It also notifies the receiver if the 
connection is lost.

A receiver must implement the functions rx_bytes() and connection_lost().

On the send side, the ProtocolAdapter simply passes on the string of bytes
presented to it to the transport.

Then name of the ProtocolAdapter reflects the effort to integrate the twisted
framework into the existing BitTorrent structure.
"""

from twisted.internet import protocol

class ProtocolAdapter(protocol.Protocol):
    def __init__(self, receiver):
        self._receiver = receiver

    def set_receiver(self, receiver):
        self._receiver = receiver

    def unset_receiver(self):
        self._receiver = None

    def dataReceived(self, data):
        if self._receiver:
            buf = buffer(data)
            offset = 0
            while offset < len(buf):
                view, size = self._receiver.get_rx_buffer()
                n = min(size, len(buf) - offset)

                view[:n] = buf[offset:offset+n]
                offset += n
                self._receiver.rx_bytes(n)

    def connectionMade(self):
        if self._receiver:
            self._receiver.connection_complete(self)

    def connectionLost(self, reason):
        if self._receiver:
            self._receiver.connection_lost()

    def tx_bytes(self, bytestr):
        self.transport.write(bytestr)

    def stop(self):
        self.transport.loseConnection()

class ProtocolAdapterFactory(protocol.Factory):
    def __init__(self, requestor):
        self._requestor = requestor

    def buildProtocol(self, addr):
        return ProtocolAdapter(self._requestor)


