import struct
import time
from handshaketranslator import HandshakeTranslator
from mock import Mock

class TestHandshakeTranslator:
    def setup_class(self):
        self.translator = HandshakeTranslator()
   
        self.protocol = struct.pack('B19c',19,*list('BitTorrent protocol'))
        self.reserved = struct.pack('8B',*([0]*8))
        self.info_hash = "\xf3l\x92\xa8\xf7\x8a\x1a\xffp\xa6\x1a_[\xfe^gW\x17a3"
        self.peer_id = "-HS0001-"+str(int(time.time())).zfill(12)
        self.handshake_str = self.protocol+self.reserved+self.info_hash+self.peer_id
        self.handshake_ba = bytearray(self.handshake_str)

    def rx_handshake(self):
        sent = 0
        while sent != len(self.handshake_ba):
            buf, needed = self.translator.get_rx_buffer()
            buf[:needed] = self.handshake_ba[sent:sent+needed]
            sent = sent+needed
            self.translator.rx_bytes(needed)

    def test_rx_handshake(self):
        self.rx_handshake()

        receiver = Mock()
        self.translator.set_receiver(receiver)
        self.rx_handshake()
        receiver.rx_handshake.assert_called_with(self.reserved,
                self.info_hash, self.peer_id)

        self.translator.unset_receiver()
        self.rx_handshake()
        assert receiver.rx_handshake.call_count == 1

    def test_rx_handshake_in_parts(self):
        receiver = Mock()
        self.translator.set_receiver(receiver)
        sent = 0
        while sent != len(self.handshake_ba):
            buf, needed = self.translator.get_rx_buffer()
            if needed > 1:
                buf[:needed-1] = self.handshake_ba[sent:sent+needed-1]
                sent = sent+needed-1
                self.translator.rx_bytes(needed-1)
            else:
                buf[:needed] = self.handshake_ba[sent:sent+needed]
                sent = sent+needed
                self.translator.rx_bytes(needed)

        receiver.rx_handshake.assert_called_with(self.reserved,
                self.info_hash, self.peer_id)

    def test_tx_handshake(self):
        self.translator.tx_handshake(self.reserved, self.info_hash, self.peer_id)

        readerwriter = Mock()
        self.translator.set_readerwriter(readerwriter)
        self.translator.tx_handshake(self.reserved, self.info_hash, self.peer_id)
        calls = readerwriter.tx_bytes.call_args_list
        assert "".join([arg[0][0] for arg in calls]) == self.handshake_str

        call_count = readerwriter.tx_bytes.call_count
        self.translator.unset_readerwriter()
        self.translator.tx_handshake(self.reserved, self.info_hash, self.peer_id)
        assert readerwriter.tx_bytes.call_count == call_count

