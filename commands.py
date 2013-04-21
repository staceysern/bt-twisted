"""
Control channel message definitions in AMP format
"""

from twisted.protocols import amp


class MsgError(Exception):
    pass


class MsgAdd(amp.Command):
    arguments = [("filename", amp.String())]
    response = [("key", amp.String())]
    errors = {MsgError: "MsgError"}


class MsgStatus(amp.Command):
    arguments = [("key", amp.String())]
    response = [("percent", amp.String())]
    errors = {MsgError: "MsgError"}


class MsgQuit(amp.Command):
    arguments = []
    response = []
