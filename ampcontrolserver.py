"""
The AMPControlServerFactory creates a AMPControlServer for each new AMP control
channel connection.  The AMPControlServer handles incoming messages by passing
them off to the client for processing and then sending the appropriate
response or error message.
"""

import commands

from twisted.internet.protocol import Factory
from twisted.protocols.amp import AMP


class AMPControlServer(AMP):
    def __init__(self, client):
        self._client = client

    @commands.MsgAdd.responder
    def add(self, filename):
        def success((info_hash, name)):
            return dict(key=info_hash)

        def failure(err):
            raise commands.MsgError(err.value.message)

        return (self._client.add_torrent(filename)
                .addCallbacks(success, failure))

    @commands.MsgStatus.responder
    def get_status(self, key):
        try:
            status = self._client.get_status(key)
        except Exception as err:
            raise commands.MsgError(err.message)

        return status

    @commands.MsgQuit.responder
    def quit(self):
        self._client.quit()
        return dict()


class AMPControlServerFactory(Factory):
    def __init__(self, client):
        self._client = client

    def buildProtocol(self, addr):
        return AMPControlServer(self._client)
