"""
The Console is a user interface for the BitTorrent client.  It interactively
accepts commands from the user and communicates with the BitTorrent client
using AMP messages over the control channel on localhost:1060.

User commands:
add [-h] [-n nickname] filename
status [-h] key
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
                                    help="filename")
        self.addparser.add_argument('-n', action='store',
                                    help="nickname", metavar="nickname")

        self.statusparser = ArgumentParser('status')
        self.statusparser.add_argument('key', action='store',
                                       help="key or nickname")

        self.nicknames = {}

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
        nickname = result['n'] if 'n' in result else ''

        if nickname in self.nicknames:
            print "Nickname {} already in use".format(nickname)
            return

        try:
            result = self.proxy.callRemote(MsgAdd, filename=filename)
        except Exception as err:
            print err.message
            return

        if nickname != '':
            self.nicknames[nickname] = result['key']

        print "Adding {} (key: {})".format(filename, result['key'])

    def do_status(self, args):
        try:
            result = vars(self.statusparser.parse_args(args.split()))
        except:
            return

        key = result['key']
        if key in self.nicknames:
            key = self.nicknames[key]

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
