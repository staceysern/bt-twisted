from mock import Mock
from trackerproxy import TrackerProxy, TrackerError
import time
import pytest
import subprocess
import signal
import os

def setup_module(module):
    global tracker
    tracker = subprocess.Popen(['python', 'faketracker.py'], stderr=1, stdout=1)

    # Give the tracker a chance to start before sending messages to it.
    time.sleep(1)

def teardown_module(module):
    os.kill(tracker.pid,signal.SIGINT)

class TestTrackerProxy:
    def setup_class(self):
        self.metainfo = Mock()
        self.trackeraddr = 'http://localhost:1061'
        self.metainfo.announce = self.trackeraddr+"/announce"
        self.metainfo.info_hash = "\xf3l\x92\xa8\xf7\x8a\x1a\xffp\xa6\x1a_[\xfe^gw\x17a3"
        self.metainfo.files = [(['file1'],750), (['file2'], 932), (['path','file3'], 382)] 
        self.peer_id = '-hs0001-'+str(int(time.time()))
    
        # This is the list of peers that the fake tracker sends
        self.peerlist =  [{'peer id': 'peer1', 'ip': '193.24.32.17', 'port': 6969},
                          {'peer id': 'peer2', 'ip': '194.25.33.18', 'port': 7070},
                          {'peer id': 'peer3', 'ip': '195.26.34.19', 'port': 7171},
                          {'peer id': 'peer4', 'ip': '196.27.35.20', 'port': 7272},
                          {'peer id': 'peer2', 'ip': '197.28.36.21', 'port': 7373}]

    def test_notracker(self):
        with pytest.raises(TrackerError) as e:
            self.metainfo.announce = "http://localhost" 
            TrackerProxy(self.metainfo, 6881, self.peer_id)
        assert e.value.message.startswith("Can't connect to the tracker")

    def test_failure(self):
        with pytest.raises(TrackerError) as e:
            self.metainfo.announce = self.trackeraddr+"/failure"
            TrackerProxy(self.metainfo, 6881, self.peer_id)
        assert e.value.message.startswith("Failure reason:")

    def test_warning(self, capsys):
        self.metainfo.announce = self.trackeraddr+"/warning"
        tp = TrackerProxy(self.metainfo, 6881, self.peer_id)
        _, err = capsys.readouterr()
        assert "Warning:" in err
        assert tp.get_peers(5) == self.peerlist 
        
    def test_announce(self):
        self.metainfo.announce = self.trackeraddr+"/announce"
        tp = TrackerProxy(self.metainfo, 6881, self.peer_id)
        assert tp.get_peers(5) == self.peerlist
        
    def test_get_peers(self):
        self.metainfo.announce = self.trackeraddr+"/announce"

        tp = TrackerProxy(self.metainfo, 6881, self.peer_id)
        assert tp.get_peers(10) == self.peerlist 

        tp = TrackerProxy(self.metainfo, 6881, self.peer_id)
        assert tp.get_peers(2) == self.peerlist[:2] 
        assert tp.get_peers(2) == self.peerlist[2:4] 
        assert tp.get_peers(2) == self.peerlist[4:] 

    
