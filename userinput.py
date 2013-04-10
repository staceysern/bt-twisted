"""
UserInput makes standard input non-blocking and registers with the Reactor to
be notified when it is ready to be read.  It interprets the input as the name
of a torrent file and notifies the client to add the torrent.

This is not the best way to get user input as it makes stdin non-blocking
for everything on the computer.
"""

import fcntl
import logging
import os
import sys

logger = logging.getLogger('bt.userinput')

class UserInput(object):
    def __init__(self, client, reactor):
        self._client = client

        fd = sys.stdin.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        reactor.register_for_read_events(self)

    def stream(self):
        return sys.stdin

    def read_event(self):
        filename = sys.stdin.read()
        self._client.add_torrent(filename[:-1])
