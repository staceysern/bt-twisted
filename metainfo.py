"""
The Metainfo reads and parses a torrent file and makes the information
available via properties.  Upon initialization, Metainfo raises an exception if
the specified file doesn't exist (IOError) or is not a valid bencoded
BitTorrent metainfo file (ValueError).

The SHA1 hash is currently computed on the info key which is bencoded after
previously having been bdecoded.  This is probably not the right way to do it
because if the order of the keys is different from the original the hash will
be different.
"""

import bencode
import hashlib


class Metainfo(object):
    def __init__(self, filename):
        metafile = open(filename, 'rb')

        try:
            self._metainfo = bencode.bdecode(metafile.read())
        except bencode.BTFailure:
            raise ValueError("Invalid BitTorrent metainfo file format")

        if 'announce' not in self._metainfo or 'info' not in self._metainfo:
            raise ValueError("Invalid BitTorrent metainfo file format")

        info = self._metainfo['info']
        if ('piece length' not in info
                or 'pieces' not in info
                or 'name' not in info):
            raise ValueError("Invalid BitTorrent metainfo file format")

        try:
            if 'length' in info:
                # Single file mode
                self._directory = ''
                self._files = [([info['name']], info['length'])]
                self._length = info['length']
            else:
                # Multi file mode
                self._directory = info['name']
                self._files = [(d['path'], d['length'])
                               for d in self._metainfo['info']['files']]
                self._length = sum([length for (_, length) in self._files])
        except:
            raise ValueError("Invalid BitTorrent metainfo file format")

        self._hash = hashlib.sha1(bencode.bencode(info)).digest()

        self._num_pieces = len(self._metainfo['info']['pieces'])/20

    @property
    def announce(self):
        return self._metainfo['announce']

    @property
    def announce_list(self):
        return self._metainfo.get('announce-list', None)

    @property
    def creation_date(self):
        return self._metainfo.get('creation date', None)

    @property
    def comment(self):
        return self._metainfo.get('comment', "")

    @property
    def created_by(self):
        return self._metainfo.get('created by', "")

    @property
    def encoding(self):
        return self._metainfo.get('encoding', "")

    @property
    def total_length(self):
        return self._length

    @property
    def piece_length(self):
        return self._metainfo['info']['piece length']

    @property
    def num_pieces(self):
        return self._num_pieces

    def piece_hash(self, index):
        if index <= self._num_pieces:
            return self._metainfo['info']['pieces'][index*20:index*20+20]
        else:
            raise IndexError("{} out of range".format(index))

    @property
    def private(self):
        return self._metainfo['info'].get('private', None)

    @property
    def directory(self):
        return self._directory

    @property
    def files(self):
        return self._files

    @property
    def info_hash(self):
        return self._hash
