"""
The HTTPControlServer manages an HTTP control channel for a client.  It
implements HTTP route handlers using the Klein microframework.  It handles
incoming messages by passing them off to the client for processing and then
sending the appropriate HTTP response.
"""

import json

from commands import MsgError
from klein import Klein
from twisted.web.static import File


class HTTPControlServer(object):
    app = Klein()

    def __init__(self, client):
        self._client = client

    @app.route('/', branch=True)
    def static(self, request):
        """
        For get requests to /, this route handler responds with the file
        static/index.html.  For get requests to /path, aside from those defined
        below (e.g. /torrents), the route handler responds with the file
        static/path.
        """
        return File("./static")

    @app.route('/torrents')
    def torrents(self, request):
        """
        The route handler for get requests to /torrents responds with a json
        formatted string which represents a dictionary containing information
        about torrents which the client is handling keyed by info hash.
        """
        return json.dumps(self._client.get_torrents())

    @app.route('/add', methods=['POST'])
    def add(self, request):
        """
        The route handler for post requests to /add asks the client to start
        handling the torrent specified by the filename supplied in the header.
        If successful, it sends a response with a key for the torrent, the name
        of the torrent and the request id that was supplied in the post
        request.  If unsuccessful, it responds with a 400 status code and a
        json formatted string containing an error message and the request id.
        """
        filename = request.args.get('filename', [''])[0]
        requestid = request.args.get('requestid', [''])[0]

        request.setHeader('Content-Type', 'application/json')

        try:
            (key, name) = self._client.add_torrent(filename)
        except MsgError as err:
            request.setResponseCode(400)
            return json.dumps(dict(message=err.message,
                                   requestid=requestid))

        return json.dumps(dict(key=key, name=name, requestid=requestid))

    @app.route('/status')
    def status(self, request):
        """
        The route handler for get requests to /status asks the client for the
        status of the torrent with the supplied key.  It responds with a json
        formatted string which represents status information about the torrent,
        currently only the percent downloaded.  If the client is not handling
        a torrent with the specified key, it responds with a 400 status code
        along with a json formatted string containing the error message.
        """
        key = request.args.get('key', [""])[0]
        request.setHeader('Content-Type', 'application/json')

        try:
            percent = self._client.get_status(key)
        except MsgError as err:
            request.setResponseCode(400)
            return json.dumps(dict(message=err.message))

        return json.dumps(dict(percent=percent))

    @app.route('/quit', methods=['POST'])
    def quit(self, request):
        """
        The route handler for post requests to /quit asks the client to shut
        down.
        """
        self._client.quit()
