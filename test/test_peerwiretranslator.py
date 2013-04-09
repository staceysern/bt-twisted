from bitstring import BitArray
import struct
from peerwiretranslator import PeerWireTranslator
from mock import Mock
import pdb

_MSG_CHOKE =            0
_MSG_UNCHOKE =          1
_MSG_INTERESTED =       2
_MSG_NOT_INTERESTED =   3
_MSG_HAVE =             4
_MSG_BITFIELD =         5
_MSG_REQUEST =          6
_MSG_PIECE =            7
_MSG_CANCEL =           8
_MSG_INVALID =          99

class TestPeerWireTranslator(object):
    def setup_class(self):
        self.translator = PeerWireTranslator()

        self.msg_keep_alive = struct.pack('B', 0)
        self.msg_choke = struct.pack('>IB', 1, _MSG_CHOKE)
        self.msg_unchoke = struct.pack('>IB', 1, _MSG_UNCHOKE)
        self.msg_interested = struct.pack('>IB', 1, _MSG_INTERESTED)
        self.msg_not_interested = struct.pack('>IB', 1, _MSG_NOT_INTERESTED)

        self.have_index = 55
        self.msg_have = struct.pack('>IBI', 5, _MSG_HAVE, self.have_index)

        self.bits = BitArray('0x123456789abcdef')
        bitsasbytes = self.bits.tobytes()
        length = len(bitsasbytes)
        self.msg_bitfield = struct.pack('>IB{}s'.format(length),
                                        1+length,  _MSG_BITFIELD, bitsasbytes)

        self.request_index = 10
        self.request_begin = 60
        self.request_length = 255
        self.msg_request = struct.pack('>IB3I', 13, _MSG_REQUEST, self.request_index, 
                                       self.request_begin, self.request_length)

        self.piece_index = 17
        self.piece_begin = 245
        self.piece_block = """Four score and seven years ago our fathers brought forth on this
        continent a new nation, conceived in liberty, and dedicated to the
        proposition that all men are created equal.
        Now we are engaged in a great civil war, testing whether that nation,
        or any nation so conceived and so dedicated, can long endure. We are
        met on a great battle-field of that war. We have come to dedicate a
        portion of that field, as a final resting place for those who here gave
        their lives that that nation might live. It is altogether fitting and
        proper that we should do this.
        But, in a larger sense, we can not dedicate, we can not consecrate, we
        can not hallow this ground. The brave men, living and dead, who
        struggled here, have consecrated it, far above our poor power to add or
        detract. The world will little note, nor long remember what we say
        here, but it can never forget what they did here. It is for us the
        living, rather, to be dedicated here to the unfinished work which they
        who fought here have thus far so nobly advanced. It is rather for us to
        be here dedicated to the great task remaining before us—that from these
        honored dead we take increased devotion to that cause for which they
        gave the last full measure of devotion—that we here highly resolve that
        these dead shall not have died in vain—that this nation, under God,
        shall have a new birth of freedom—and that government of the people, by
        the people, for the people, shall not perish from the earth."""
        length = len(self.piece_block)
        self.msg_piece = struct.pack('>IB2I{}s'.format(length), 9+length, 
                                     _MSG_PIECE, self.piece_index, 
                                     self.piece_begin, self.piece_block)

        self.cancel_index = 99
        self.cancel_begin = 128
        self.cancel_length = 13
        self.msg_cancel = struct.pack('>IB3I', 13, _MSG_CANCEL, self.cancel_index, 
                                      self.cancel_begin, self.cancel_length)

        self.junk = "abcdefghijklmnop"
        length = len(self.junk)
        self.msg_invalid = struct.pack('>IB{}s'.format(length), 1+length,
                                       _MSG_INVALID, self.junk)

    def rx_bytes(self, string): 
        message = bytearray(string)
        sent = 0
        while sent != len(message):
            buf, needed = self.translator.get_rx_buffer()
            buf[:needed] = message[sent:sent+needed]
            sent = sent+needed
            self.translator.rx_bytes(needed)

    def rx_bytes_in_parts(self, string): 
        message = bytearray(string)
        sent = 0
        while sent != len(message):
            buf, needed = self.translator.get_rx_buffer()
            if needed > 1:
                buf[:needed-1] = message[sent:sent+needed-1]
                sent = sent+needed-1
                self.translator.rx_bytes(needed-1)
            else:
                buf[:needed] = message[sent:sent+needed]
                sent = sent+needed
                self.translator.rx_bytes(needed)

                """
    def test_keep_alive(self):
        self.rx_bytes(self.msg_keep_alive)

        self.translator.set_receiver(self.receiver)
        self.rx_bytes(self.msg_keep_alive)
        assert self.receiver.rx_keep_alive.called

        call_count = self.receiver.rx_keep_alive.call_count
        self.translator.unset_receiver()
        self.rx_bytes(self.msg_keep_alive)
        assert self.receiver.rx_keep_alive.call_count == call_count 
        """

    def test_rx_choke(self):
        self.rx_bytes(self.msg_choke)

        self.receiver = Mock()
        self.translator.set_receiver(self.receiver)
        self.rx_bytes(self.msg_choke)
        assert self.receiver.rx_choke.called

        call_count = self.receiver.rx_choke.call_count
        self.rx_bytes_in_parts(self.msg_choke)
        assert self.receiver.rx_choke.call_count == call_count+1
        
        call_count = self.receiver.rx_choke.call_count
        self.translator.unset_receiver()
        self.rx_bytes(self.msg_choke)
        assert self.receiver.rx_choke.call_count == call_count 

    def test_rx_unchoke(self):
        self.rx_bytes(self.msg_unchoke)

        self.receiver = Mock()
        self.translator.set_receiver(self.receiver)
        self.rx_bytes(self.msg_unchoke)
        assert self.receiver.rx_unchoke.called

        call_count = self.receiver.rx_unchoke.call_count
        self.rx_bytes_in_parts(self.msg_unchoke)
        assert self.receiver.rx_unchoke.call_count == call_count+1

        call_count = self.receiver.rx_unchoke.call_count
        self.translator.unset_receiver()
        self.rx_bytes(self.msg_unchoke)
        assert self.receiver.rx_unchoke.call_count == call_count 

    def test_rx_interested(self):
        self.rx_bytes(self.msg_interested)

        self.receiver = Mock()
        self.translator.set_receiver(self.receiver)
        self.rx_bytes(self.msg_interested)
        assert self.receiver.rx_interested.called

        call_count = self.receiver.rx_interested.call_count
        self.rx_bytes_in_parts(self.msg_interested)
        assert self.receiver.rx_interested.call_count == call_count+1

        call_count = self.receiver.rx_interested.call_count
        self.translator.unset_receiver()
        self.rx_bytes(self.msg_interested)
        assert self.receiver.rx_interested.call_count == call_count

    def test_rx_not_interested(self):
        self.rx_bytes(self.msg_not_interested)

        self.receiver = Mock()
        self.translator.set_receiver(self.receiver)
        self.rx_bytes(self.msg_not_interested)
        assert self.receiver.rx_not_interested.called

        call_count = self.receiver.rx_not_interested.call_count
        self.rx_bytes_in_parts(self.msg_not_interested)
        assert self.receiver.rx_not_interested.call_count == call_count+1

        call_count = self.receiver.rx_not_interested.call_count
        self.translator.unset_receiver()
        self.rx_bytes(self.msg_not_interested)
        assert self.receiver.rx_not_interested.call_count == call_count

    def test_rx_have(self):
        self.rx_bytes(self.msg_have)

        self.receiver = Mock()
        self.translator.set_receiver(self.receiver)
        self.rx_bytes(self.msg_have)
        self.receiver.rx_have.assert_called_with(self.have_index)

        self.receiver = Mock()
        self.translator.set_receiver(self.receiver)
        self.rx_bytes_in_parts(self.msg_have)
        self.receiver.rx_have.assert_called_with(self.have_index)

        call_count = self.receiver.rx_have.call_count
        self.translator.unset_receiver()
        self.rx_bytes(self.msg_have)
        assert self.receiver.rx_have.call_count == call_count

    def test_rx_bitfield(self):
        self.rx_bytes(self.msg_bitfield)

        self.receiver = Mock()
        self.translator.set_receiver(self.receiver)
        self.rx_bytes(self.msg_bitfield)
        bits = self.receiver.rx_bitfield.call_args_list[0][0][0]
        assert bits.tobytes() == self.bits.tobytes()

        self.receiver = Mock()
        self.translator.set_receiver(self.receiver)
        self.rx_bytes_in_parts(self.msg_bitfield)
        bits = self.receiver.rx_bitfield.call_args_list[0][0][0]
        assert bits.tobytes() == self.bits.tobytes()

        call_count = self.receiver.rx_bitfield.call_count
        self.translator.unset_receiver()
        self.rx_bytes(self.msg_bitfield)
        assert self.receiver.rx_bitfield.call_count == call_count

    def test_rx_request(self):
        self.rx_bytes(self.msg_request)

        self.receiver = Mock()
        self.translator.set_receiver(self.receiver)
        self.rx_bytes(self.msg_request)
        self.receiver.rx_request.assert_called_with(self.request_index,
                self.request_begin, self.request_length)
        
        self.receiver = Mock()
        self.translator.set_receiver(self.receiver)
        self.rx_bytes_in_parts(self.msg_request)
        self.receiver.rx_request.assert_called_with(self.request_index,
                self.request_begin, self.request_length)

        call_count = self.receiver.rx_request.call_count
        self.translator.unset_receiver()
        self.rx_bytes(self.msg_request)
        assert self.receiver.rx_request.call_count == call_count
        
    def test_rx_piece(self):
        self.rx_bytes(self.msg_piece)

        self.receiver = Mock()
        self.translator.set_receiver(self.receiver)
        self.rx_bytes(self.msg_piece)
        args = self.receiver.rx_piece.call_args_list[0][0]
        assert args[0] == self.piece_index
        assert args[1] == self.piece_begin
        for i in range(len(args[2])):
            assert args[2][i] == self.piece_block[i]
        print self.piece_block

        self.receiver = Mock()
        self.translator.set_receiver(self.receiver)
        self.rx_bytes_in_parts(self.msg_piece)
        args = self.receiver.rx_piece.call_args_list[0][0]
        assert args[0] == self.piece_index
        assert args[1] == self.piece_begin
        for i in range(len(args[2])):
            assert args[2][i] == self.piece_block[i]

        call_count = self.receiver.rx_piece.call_count
        self.translator.unset_receiver()
        self.rx_bytes(self.msg_piece)
        assert self.receiver.rx_piece.call_count == call_count

    def test_rx_cancel(self):
        self.rx_bytes(self.msg_cancel)

        self.receiver = Mock()
        self.translator.set_receiver(self.receiver)
        self.rx_bytes(self.msg_cancel)
        self.receiver.rx_cancel.assert_called_with(self.cancel_index,
                self.cancel_begin, self.cancel_length)

        self.receiver = Mock()
        self.translator.set_receiver(self.receiver)
        self.rx_bytes_in_parts(self.msg_cancel)
        self.receiver.rx_cancel.assert_called_with(self.cancel_index,
                self.cancel_begin, self.cancel_length)

        call_count = self.receiver.rx_cancel.call_count
        self.translator.unset_receiver()
        self.rx_bytes(self.msg_cancel)
        assert self.receiver.rx_cancel.call_count == call_count
     
    def test_rx_invalid(self):
        self.rx_bytes(self.msg_invalid)

        self.receiver = Mock()
        self.translator.set_receiver(self.receiver)
        self.rx_bytes(self.msg_invalid)

        self.receiver = Mock()
        self.translator.set_receiver(self.receiver)
        self.rx_bytes_in_parts(self.msg_invalid)

        self.translator.unset_receiver()
        self.rx_bytes(self.msg_invalid)
     
    def test_tx_keep_alive(self):
        self.translator.tx_keep_alive()

        self.readerwriter = Mock()
        self.translator.set_readerwriter(self.readerwriter)
        self.translator.tx_keep_alive()
        
        calls = self.readerwriter.tx_bytes.call_args_list
        assert "".join([arg[0][0] for arg in calls]) == self.msg_keep_alive

        call_count = self.readerwriter.tx_bytes.call_count
        self.translator.unset_readerwriter()
        self.translator.tx_keep_alive()
        assert self.readerwriter.tx_bytes.call_count == call_count

    def test_tx_choke(self):
        self.translator.tx_choke()

        self.readerwriter = Mock()
        self.translator.set_readerwriter(self.readerwriter)
        self.translator.tx_choke()
        
        calls = self.readerwriter.tx_bytes.call_args_list
        assert "".join([arg[0][0] for arg in calls]) == self.msg_choke

        call_count = self.readerwriter.tx_bytes.call_count
        self.translator.unset_readerwriter()
        self.translator.tx_choke()
        assert self.readerwriter.tx_bytes.call_count == call_count

    def test_tx_unchoke(self):
        self.translator.tx_unchoke()

        self.readerwriter = Mock()
        self.translator.set_readerwriter(self.readerwriter)
        self.translator.tx_unchoke()
        
        calls = self.readerwriter.tx_bytes.call_args_list
        assert "".join([arg[0][0] for arg in calls]) == self.msg_unchoke

        call_count = self.readerwriter.tx_bytes.call_count
        self.translator.unset_readerwriter()
        self.translator.tx_unchoke()
        assert self.readerwriter.tx_bytes.call_count == call_count

    def test_tx_interested(self):
        self.translator.tx_interested()

        self.readerwriter = Mock()
        self.translator.set_readerwriter(self.readerwriter)
        self.translator.tx_interested()
        
        calls = self.readerwriter.tx_bytes.call_args_list
        assert "".join([arg[0][0] for arg in calls]) == self.msg_interested

        call_count = self.readerwriter.tx_bytes.call_count
        self.translator.unset_readerwriter()
        self.translator.tx_interested()
        assert self.readerwriter.tx_bytes.call_count == call_count

    def test_tx_not_interested(self):
        self.translator.tx_not_interested()

        self.readerwriter = Mock()
        self.translator.set_readerwriter(self.readerwriter)
        self.translator.tx_not_interested()
        
        calls = self.readerwriter.tx_bytes.call_args_list
        assert "".join([arg[0][0] for arg in calls]) == self.msg_not_interested

        call_count = self.readerwriter.tx_bytes.call_count
        self.translator.unset_readerwriter()
        self.translator.tx_not_interested()
        assert self.readerwriter.tx_bytes.call_count == call_count

    def test_tx_have(self):
        self.translator.tx_have(self.have_index)

        self.readerwriter = Mock()
        self.translator.set_readerwriter(self.readerwriter)
        self.translator.tx_have(self.have_index)
        
        calls = self.readerwriter.tx_bytes.call_args_list
        assert "".join([arg[0][0] for arg in calls]) == self.msg_have

        call_count = self.readerwriter.tx_bytes.call_count
        self.translator.unset_readerwriter()
        self.translator.tx_have(self.have_index)
        assert self.readerwriter.tx_bytes.call_count == call_count

    def test_tx_bitfield(self):
        self.translator.tx_bitfield(self.bits)

        self.readerwriter = Mock()
        self.translator.set_readerwriter(self.readerwriter)
        self.translator.tx_bitfield(self.bits)
        
        calls = self.readerwriter.tx_bytes.call_args_list
        assert "".join([arg[0][0] for arg in calls]) == self.msg_bitfield

        call_count = self.readerwriter.tx_bytes.call_count
        self.translator.unset_readerwriter()
        self.translator.tx_bitfield(self.bits)
        assert self.readerwriter.tx_bytes.call_count == call_count

    def test_tx_request(self):
        self.translator.tx_request(self.request_index, self.request_begin, self.request_length)

        self.readerwriter = Mock()
        self.translator.set_readerwriter(self.readerwriter)
        self.translator.tx_request(self.request_index, self.request_begin, self.request_length)
        
        calls = self.readerwriter.tx_bytes.call_args_list
        assert "".join([arg[0][0] for arg in calls]) == self.msg_request

        call_count = self.readerwriter.tx_bytes.call_count
        self.translator.unset_readerwriter()
        self.translator.tx_request(self.request_index, self.request_begin, self.request_length)
        assert self.readerwriter.tx_bytes.call_count == call_count

    def test_tx_piece(self):
        self.translator.tx_piece(self.piece_index, self.piece_begin, self.piece_block)

        self.readerwriter = Mock()
        self.translator.set_readerwriter(self.readerwriter)
        self.translator.tx_piece(self.piece_index, self.piece_begin, self.piece_block)
        
        calls = self.readerwriter.tx_bytes.call_args_list
        assert "".join([arg[0][0] for arg in calls]) == self.msg_piece

        call_count = self.readerwriter.tx_bytes.call_count
        self.translator.unset_readerwriter()
        self.translator.tx_piece(self.piece_index, self.piece_begin, self.piece_block)
        assert self.readerwriter.tx_bytes.call_count == call_count

    def test_tx_cancel(self):
        self.translator.tx_cancel(self.cancel_index, self.cancel_begin, self.cancel_length)

        self.readerwriter = Mock()
        self.translator.set_readerwriter(self.readerwriter)
        self.translator.tx_cancel(self.cancel_index, self.cancel_begin, self.cancel_length)
        
        calls = self.readerwriter.tx_bytes.call_args_list
        assert "".join([arg[0][0] for arg in calls]) == self.msg_cancel

        call_count = self.readerwriter.tx_bytes.call_count
        self.translator.unset_readerwriter()
        self.translator.tx_cancel(self.cancel_index, self.cancel_begin, self.cancel_length)
        assert self.readerwriter.tx_bytes.call_count == call_count

    def test_tx_keep_alive(self):
        self.translator.tx_keep_alive()

        self.readerwriter = Mock()
        self.translator.set_readerwriter(self.readerwriter)
        self.translator.tx_keep_alive()
        
        calls = self.readerwriter.tx_bytes.call_args_list
        assert "".join([arg[0][0] for arg in calls]) == self.msg_keep_alive

        call_count = self.readerwriter.tx_bytes.call_count
        self.translator.unset_readerwriter()
        self.translator.tx_keep_alive()
        assert self.readerwriter.tx_bytes.call_count == call_count

    def test_tx_choke(self):
        self.translator.tx_choke()

        self.readerwriter = Mock()
        self.translator.set_readerwriter(self.readerwriter)
        self.translator.tx_choke()
        
        calls = self.readerwriter.tx_bytes.call_args_list
        assert "".join([arg[0][0] for arg in calls]) == self.msg_choke

        call_count = self.readerwriter.tx_bytes.call_count
        self.translator.unset_readerwriter()
        self.translator.tx_choke()
        assert self.readerwriter.tx_bytes.call_count == call_count

    def test_tx_unchoke(self):
        self.translator.tx_unchoke()

        self.readerwriter = Mock()
        self.translator.set_readerwriter(self.readerwriter)
        self.translator.tx_unchoke()
        
        calls = self.readerwriter.tx_bytes.call_args_list
        assert "".join([arg[0][0] for arg in calls]) == self.msg_unchoke

        call_count = self.readerwriter.tx_bytes.call_count
        self.translator.unset_readerwriter()
        self.translator.tx_unchoke()
        assert self.readerwriter.tx_bytes.call_count == call_count

    def test_tx_interested(self):
        self.translator.tx_interested()

        self.readerwriter = Mock()
        self.translator.set_readerwriter(self.readerwriter)
        self.translator.tx_interested()
        
        calls = self.readerwriter.tx_bytes.call_args_list
        assert "".join([arg[0][0] for arg in calls]) == self.msg_interested

        call_count = self.readerwriter.tx_bytes.call_count
        self.translator.unset_readerwriter()
        self.translator.tx_interested()
        assert self.readerwriter.tx_bytes.call_count == call_count

    def test_tx_not_interested(self):
        self.translator.tx_not_interested()

        self.readerwriter = Mock()
        self.translator.set_readerwriter(self.readerwriter)
        self.translator.tx_not_interested()
        
        calls = self.readerwriter.tx_bytes.call_args_list
        assert "".join([arg[0][0] for arg in calls]) == self.msg_not_interested

        call_count = self.readerwriter.tx_bytes.call_count
        self.translator.unset_readerwriter()
        self.translator.tx_not_interested()
        assert self.readerwriter.tx_bytes.call_count == call_count

    def test_tx_have(self):
        self.translator.tx_have(self.have_index)

        self.readerwriter = Mock()
        self.translator.set_readerwriter(self.readerwriter)
        self.translator.tx_have(self.have_index)
        
        calls = self.readerwriter.tx_bytes.call_args_list
        assert "".join([arg[0][0] for arg in calls]) == self.msg_have

        call_count = self.readerwriter.tx_bytes.call_count
        self.translator.unset_readerwriter()
        self.translator.tx_have(self.have_index)
        assert self.readerwriter.tx_bytes.call_count == call_count

    def test_tx_bitfield(self):
        self.translator.tx_bitfield(self.bits)

        self.readerwriter = Mock()
        self.translator.set_readerwriter(self.readerwriter)
        self.translator.tx_bitfield(self.bits)
        
        calls = self.readerwriter.tx_bytes.call_args_list
        assert "".join([arg[0][0] for arg in calls]) == self.msg_bitfield

        call_count = self.readerwriter.tx_bytes.call_count
        self.translator.unset_readerwriter()
        self.translator.tx_bitfield(self.bits)
        assert self.readerwriter.tx_bytes.call_count == call_count

    def test_tx_request(self):
        self.translator.tx_request(self.request_index, self.request_begin, self.request_length)

        self.readerwriter = Mock()
        self.translator.set_readerwriter(self.readerwriter)
        self.translator.tx_request(self.request_index, self.request_begin, self.request_length)
        
        calls = self.readerwriter.tx_bytes.call_args_list
        assert "".join([arg[0][0] for arg in calls]) == self.msg_request

        call_count = self.readerwriter.tx_bytes.call_count
        self.translator.unset_readerwriter()
        self.translator.tx_request(self.request_index, self.request_begin, self.request_length)
        assert self.readerwriter.tx_bytes.call_count == call_count

    def test_tx_piece(self):
        self.translator.tx_piece(self.piece_index, self.piece_begin, self.piece_block)

        self.readerwriter = Mock()
        self.translator.set_readerwriter(self.readerwriter)
        self.translator.tx_piece(self.piece_index, self.piece_begin, self.piece_block)
        
        calls = self.readerwriter.tx_bytes.call_args_list
        assert "".join([arg[0][0] for arg in calls]) == self.msg_piece

        call_count = self.readerwriter.tx_bytes.call_count
        self.translator.unset_readerwriter()
        self.translator.tx_piece(self.piece_index, self.piece_begin, self.piece_block)
        assert self.readerwriter.tx_bytes.call_count == call_count

    def test_tx_cancel(self):
        self.translator.tx_cancel(self.cancel_index, self.cancel_begin, self.cancel_length)

        self.readerwriter = Mock()
        self.translator.set_readerwriter(self.readerwriter)
        self.translator.tx_cancel(self.cancel_index, self.cancel_begin, self.cancel_length)
        
        calls = self.readerwriter.tx_bytes.call_args_list
        assert "".join([arg[0][0] for arg in calls]) == self.msg_cancel

        call_count = self.readerwriter.tx_bytes.call_count
        self.translator.unset_readerwriter()
        self.translator.tx_cancel(self.cancel_index, self.cancel_begin, self.cancel_length)
        assert self.readerwriter.tx_bytes.call_count == call_count

