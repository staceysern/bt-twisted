"""
The Console is a user interface for the BitTorrent client.  It interactively
accepts commands from the user and communicates with the BitTorrent client
using AMP messages over the control channel on localhost:1060.

User commands:
add [-h] metafile
status [-h] metafile
quit
"""

import sys

from ampy import ampy
from argparse import ArgumentParser
from cmd import Cmd

# Control channel message definitions in ampy format

class MsgError:
    pass


class MsgAdd(ampy.Command):
    arguments = [("filename", ampy.String())]
    response = [("key", ampy.String())]
    errors = {MsgError: "MsgError"}


class MsgStatus(ampy.Command):
    arguments = [("key", ampy.String())]
    response = [("percent", ampy.String())]
    errors = {MsgError: "MsgError"}


class MsgQuit(ampy.Command):
    arguments = []


class Console(Cmd):
    prompt = "BT Console: "
    intro = "BitTorrent Console"

    def __init__(self):
        Cmd.__init__(self)

        self.addparser = ArgumentParser('add')
        self.addparser.add_argument('filename', action='store',
                                    help="metainfo filename")

        self.statusparser = ArgumentParser('status')
        self.statusparser.add_argument('key', action='store',
                                       help="20 character hash")

        self.proxy = ampy.Proxy('localhost', 1060)
        try:
            self.proxy.connect()
        except:
            print "Unable to connect to localhost:1060"
            sys.exit(1)

    def do_add(self, args):
        try:
            result = vars(self.addparser.parse_args(args.split()))
        except:
            return

        filename = result['filename']

        try:
            result = self.proxy.callRemote(MsgAdd, filename=filename)
        except Exception as err:
            print err.message
            return

        print "Adding {} (key: {})".format(filename, result['key']) 

    def do_status(self, args):
        try:
            result = vars(self.statusparser.parse_args(args.split()))
        except:
            return

        key = result['key']

        try:
            result = self.proxy.callRemote(MsgStatus, key=key)
        except Exception as err:
            print err.message
            return

        print result['percent'] + "% downloaded"

    def do_quit(self, args):
        self.proxy.callRemoteNoAnswer(MsgQuit)
        sys.exit()

    def do_EOF(self, line):
        return True

    def help_add(self):
        self.addparser.print_help()

    def help_status(self):
        self.statusparser.print_help()

    def postloop(self):
        print

if __name__ == '__main__':
    Console().cmdloop()
