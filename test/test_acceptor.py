import socket
import select
from mock import Mock
from acceptor import Acceptor

PORT = 59695

class TestAcceptor:
    def setup_class(self):
        self.receiver = Mock()
        self.acceptor = Acceptor(('127.0.0.1', PORT), self.receiver)
        
    def test_stream(self):
        assert self.acceptor.stream().getsockname() == ('127.0.0.1', PORT)

    def test_accept(self):
        peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer.setblocking(0)
        try:
            peer.connect(('127.0.0.1', PORT))
        except Exception as e:
            err = peer.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            if err != 0 and err != errno.EINPROGRESS:
                raise e

        select.select([self.acceptor.stream()],[],[])
        self.acceptor.read_event()

        assert self.receiver.accepted_connection.called
