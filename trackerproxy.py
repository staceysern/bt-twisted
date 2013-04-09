"""
The TrackerProxy contacts the tracker specified in the supplied MetaInfo object
and provides information about peers upon request.  During initialization, the
TrackerProxy raises a TrackereError if the tracker can't be contacted or
returns an invalid response.

This blocking TrackerProxy should be made non-blocking.  

Right now, this client doesn't support multiple trackers specified by 
announce-list in the Metainfo object.

If the peer list is exhausted, should the TrackerProxy go back and get more
peers from the tracker?  Should the TrackerProxy report periodically back to
the tracker reflecting its progress in downloading the file?
"""

import bencode
import logging
import metainfo
import requests
import sys

logger = logging.getLogger('bt.trackerproxy')

class TrackerError(Exception):
    pass

class TrackerProxy(object):
    def __init__(self, metainfo, port, peer_id):
        self._metainfo = metainfo
        self._port = port
        self._peer_id = peer_id

        params = {'info_hash': self._metainfo.info_hash, 
                  'peer_id': self._peer_id,
                  'port': self._port,
                  'uploaded': 0,
                  'downloaded': 0,
                  'left': sum([pair[1] for pair in self._metainfo.files]),
                  'compact': 1,
                  'event': 'started'
                 }

        try:
            r = requests.get(self._metainfo.announce, params=params)
        except requests.ConnectionError :
            raise TrackerError("Can't connect to the tracker at {}".
                               format(self._metainfo.announce))

        response = bencode.bdecode(r.content)

        if 'failure reason' in response:
            raise TrackerError("Failure reason: {}".
                               format(response['failure reason']))

        if 'warning message' in response:
            logger.warning("Warning: {}".format(response['warning message']))
            print >>sys.stderr, ("Warning: {}".
                                 format(response['warning message']))

        self._min_interval = response.get('min interval', 0)
        self._tracker_id = response.get('tracker id', 0)

        self._interval = response.get('interval', 0)
        self._complete = response.get('complete',0)
        self._incomplete = response.get('incomplete',0)

        if 'peers' not in response:
            raise TrackerError("Response from tracker missing peers")

        if isinstance(response['peers'], list):
            self._peers = response['peers']
        else:
            self._peers = []
            peers = response['peers']
            for offset in xrange(0, len(peers),6):
                self._peers.append({'ip': "{}.{}.{}.{}".format(
                                             str(ord(peers[offset])),
                                             str(ord(peers[offset+1])),
                                             str(ord(peers[offset+2])),
                                             str(ord(peers[offset+3]))),
                                   'port': ord(peers[offset+4])*256 +
                                           ord(peers[offset+5])})

    def get_peers(self, n):
        if (len(self._peers) <= n):
            n = len(self._peers)

        p = self._peers[:n]
        self._peers = self._peers[n:]
        return p
            

            

