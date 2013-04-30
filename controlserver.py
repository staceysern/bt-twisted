"""
The ControlServerFactory creates a ControlServer for each new AMP control
channel connection.  The ControlServer handles incoming messages by passing
them off to the client for processing and then sending the appropriate
response or error message.
"""

import commands

from twisted.internet.protocol import Factory
from twisted.protocols.amp import AMP


class ControlServer(AMP):
    def __init__(self, client):
        self._client = client

    @commands.MsgAdd.responder
    def add(self, filename):
        def success(key):
            return dict(key=key)

        def failure(err):
            raise commands.MsgError(err.value.message)

        return (self._client.add_torrent(filename)
                .addCallbacks(success, failure))

    @commands.MsgStatus.responder
    def get_status(self, key):
        return self._client.get_status(key)

    @commands.MsgQuit.responder
    def quit(self):
        self._client.quit()
        return dict()


class ControlServerFactory(Factory):
    def __init__(self, client):
        self._client = client

    def buildProtocol(self, addr):
        return ControlServer(self._client)
