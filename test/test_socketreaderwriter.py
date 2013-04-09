import select
import socket
import mock
from mock import Mock
from mock import patch
from socketreaderwriter import SocketReaderWriter
from reactor import Reactor

def setup_module(module):
    global server, rsock, wsock

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.setblocking(0)
    server.bind(('localhost', 59655))
    server.listen(1)

    try:
        wsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        wsock.setblocking(0)
        wsock.connect(('localhost', 59655))
    except Exception as e:
        err = wsock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if err != 0 and err != errno.EINPROGRESS:
            raise e

    select.select([server],[],[])
    rsock, _ = server.accept()
    select.select([],[wsock],[])

def teardown_module(module):
    wsock.close()
    rsock.close()
    server.close()

class TestSocketReaderWriter:
    def test_stream(self):
        r = SocketReaderWriter(rsock)
        assert r.stream() == rsock 

    def test_read(self):
        r = SocketReaderWriter(rsock)
        self.buffer = bytearray(100)
        self.view = memoryview(self.buffer)

        rcvr = Mock()
        rcvr.get_rx_buffer = Mock(return_value = (self.view, 100))

        string1 = "test string"
        string2 = "second test string"

        # bytes should be read only when the receiver is set
        wsock.send(string1)
        _, _, _ = select.select([rsock],[],[])
        r.read_event()
        
        r.set_receiver(rcvr)

        wsock.send(string2)

        select.select([rsock],[],[])
        r.read_event()

        total_length = len(string1)+len(string2)
        rcvr.rx_bytes.assert_called_with(total_length)
        assert self.view[0:total_length].tobytes() == string1+string2 

        # after the receiver is unset, make sure it isn't called for 
        # incoming bytes
        r.unset_receiver()
        wsock.send(string2)

        call_count = rcvr.rx_bytes.call_count 
        select.select([rsock],[],[])
        r.read_event()
        assert rcvr.rx_bytes.call_count == call_count
    
        # cleanup by reading the bytes from the socket
        r.set_receiver(rcvr)
        r.read_event()

    def test_tx_bytes(self):
        pass

    def test_write(self):
        string1 = "test string"
        string2 = "second test string"

        w = SocketReaderWriter(wsock)
        w.tx_bytes(string1)
        
        select.select([],[wsock],[])
        w.write_event()
    
        # make sure unregister_for_write_events called
        select.select([rsock],[],[])
        data = rsock.recv(65535) 
        assert data == string1 

        w.tx_bytes(string1)
        w.tx_bytes(string2)

        select.select([],[wsock],[])
        w.write_event()

        select.select([rsock],[],[])
        data = rsock.recv(len(string1)) 
        assert data == string1

        select.select([rsock],[],[])
        data = rsock.recv(len(string2)) 
        assert data == string2

    def test_partial_send(self):
        mock_sock = Mock()
        mock_sock.send = Mock(return_value = 3)

        string1 = "abcdefghi"
        w = SocketReaderWriter(mock_sock)
        w.tx_bytes(string1)

        w.write_event() 
        assert mock_sock.send.called_with(string1)

        w.write_event() 
        assert mock_sock.send.called_with(string1[3:])
    
        w.write_event() 
        assert mock_sock.send.called_with(string1[6:])

        call_count = mock_sock.send.call_count
        w.write_event()
        assert mock_sock.send.call_count == call_count

    def stop(self):
        pass
