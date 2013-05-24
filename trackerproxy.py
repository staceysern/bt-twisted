"""
The TrackerProxy contacts the tracker specified in the supplied MetaInfo object
and provides information about peers upon request.  After creation, the
TrackerProxy must be told to start at which point it attempts to contact the
tracker.  It raises a TrackerError if the tracker can't be contacted or
returns an invalid response.

Right now, this client doesn't support multiple trackers specified by
announce-list in the Metainfo object.

The TrackerProxy should periodically report progress back to the tracker and
notify it when it has downloaded the entire torrent.  If the peer list is
exhausted, it should also get more peers from the tracker.
"""

import bencode
import logging
import sys

from twisted.internet.defer import Deferred
from twisted.web.client import getPage

logger = logging.getLogger('bt.trackerproxy')


class TrackerError(Exception):
    pass


class TrackerProxy(object):
    def __init__(self, metainfo, port, peer_id):
        self._metainfo = metainfo
        self._port = port
        self._peer_id = peer_id
        self._started = False
        self._tracker_id = ""

    def _params_str(self, params_dict):
        return "&".join(str(k)+"="+str(v) for (k, v) in params_dict.items())

    def start(self):
        """
        start() begins communication with the tracker.  It returns a
        deferred which fires when a response has been received from the
        tracker and validated.  It raises a TrackerError if it can't reach
        the tracker, it receives a failure response or the response does
        not contain required fields.
        """

        params = {'info_hash': self._metainfo.info_hash,
                  'peer_id': self._peer_id,
                  'port': self._port,
                  'uploaded': 0,
                  'downloaded': 0,
                  'left': sum([pair[1] for pair in self._metainfo.files]),
                  'compact': 1,
                  'event': 'started'}

        addr = self._metainfo.announce+"?"+self._params_str(params)

        return getPage(addr).addCallbacks(self._decode, self._connect_error)

    def _connect_error(self, failure):
        raise TrackerError("Can't connect to the tracker at {}"
                           .format(self._metainfo.announce))

    def _decode(self, content):
        response = bencode.bdecode(content)

        if 'failure reason' in response:
            raise TrackerError("Failure reason: {}"
                               .format(response['failure reason']))

        if 'warning message' in response:
            logger.warning("Warning: {}".format(response['warning message']))
            print >> sys.stderr, ("Warning: {}"
                                  .format(response['warning message']))

        try:
            self._min_interval = response.get('min interval', 0)
            if 'tracker id' in response:
                self._tracker_id = response['tracker id']

            self._interval = response['interval']
            self._complete = response['complete']
            self._incomplete = response['incomplete']

            if isinstance(response['peers'], list):
                self._peers = response['peers']
            else:
                self._peers = []
                peers = response['peers']
                for offset in xrange(0, len(peers), 6):
                    self._peers.append({'ip': "{}.{}.{}.{}"
                                        .format(str(ord(peers[offset])),
                                                str(ord(peers[offset+1])),
                                                str(ord(peers[offset+2])),
                                                str(ord(peers[offset+3]))),
                                        'port': (ord(peers[offset+4])*256 +
                                                 ord(peers[offset+5]))})
        except Exception:
            raise TrackerError("Invalid tracker response")

        self._started = True

    def get_peers(self, n):
        """
        get_peers() takes a number and returns a deferred which fires when
        that number of peer addresses are available.  The TrackerProxy may
        need to request more peers from the tracker but for right now, it
        triggers the callback immediately with whatever it has.
        """
        if not self._started:
            raise TrackerError("TrackerProxy not started")

        self._n = n

        def return_peers(ignored):
            n = self._n
            del self._n

            if (len(self._peers) <= n):
                n = len(self._peers)

            peers = self._peers[:n]
            self._peers = self._peers[n:]
            return peers

        d = Deferred().addCallback(return_peers)
        d.callback(None)
        return d
