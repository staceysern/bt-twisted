from metainfo import Metainfo
import pytest

class TestMetainfo:
    def setup_class(self):
        self.singlefile = Metainfo("ubuntu.torrent")
        self.multifile = Metainfo("multi.torrent")

    def test_announce(self):
        assert self.singlefile.announce == "http://torrent.ubuntu.com:6969/announce" 

    def test_announce_list(self):
        assert self.singlefile.announce_list == [
                ['http://torrent.ubuntu.com:6969/announce'],
                ['http://ipv6.torrent.ubuntu.com:6969/announce']]

        assert self.multifile.announce_list == None

    def test_creation_date(self):
        # TODO Test a .torrent file without the optional creation date info
        assert self.singlefile.creation_date == 1350570528

    def test_comment(self):
        assert self.singlefile.comment == "Ubuntu CD releases.ubuntu.com"
        assert self.multifile.comment == ""

    def test_created_by(self):
        # TODO Test a .torrent file with the optional created by info
        assert self.singlefile.created_by ==  "" 
        
    def test_encoding(self):
        assert self.singlefile.encoding == "" 
        assert self.multifile.encoding == "UTF-8" 

    def test_piece_length(self):
        assert self.singlefile.piece_length == 524288

    def test_pieces(self):
        assert self.singlefile.num_pieces == 30520/20

    def test_piece_hash(self):
        # TODO
        pass

    def test_private(self):
        # TODO Test a .torrent file with the optional private info 
        assert self.singlefile.private == None

    def test_directory(self):
        assert self.singlefile.directory == ""
        assert self.multifile.directory == "bencode-1.0"

    def test_files(self):
        assert self.singlefile.files == [(['ubuntu-12.10-desktop-amd64.iso'],
                                          800063488)]
        assert self.multifile.files == [
                (['bencode', '__init__.py'],3305),
                (['setup.py'],850),
                (['bencode.egg-info', 'PKG-INFO'],576),
                (['PKG-INFO'],576),
                (['README.txt'],457),
                (['bencode.egg-info', 'SOURCES.txt'],204),
                (['setup.cfg'],59),
                (['bencode', 'BTL.py'],37),
                (['bencode.egg-info', 'top_level.txt'],8),
                (['bencode.egg-info', 'dependency_links.txt'],1),
                (['bencode.egg-info', 'zip-safe'],1)]

    def test_info_hash(self):
        assert self.singlefile.info_hash == "\xf3l\x92\xa8\xf7\x8a\x1a\xffp\xa6\x1a_[\xfe^gW\x17a3"

    def test_constructor(self):
        # TODO Test the constructor with additional malformed .torrent 
        # files and look for the appropriate exceptions
        with pytest.raises(IOError): 
            Metainfo("")

        with pytest.raises(ValueError):
            Metainfo("test_metainfo.py")

