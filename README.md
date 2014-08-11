## BitTorrent

A BitTorrent client written in Python using the Twisted networking library.

This version of the BitTorrent client consists of the client itself as well as a console for user control.  It can also be controlled with a javascript application in a browser.  It implements downloading but not uploading.  It can handle multiple torrents at a time but does not manage traffic load.  It uses a very simple strategy for determining which blocks to request and does not implement keep alives, pipelined requests or endgame strategy.

This BitTorrent client uses Twisted, a Python networking library.  Another version, which includes its own event loop, can be found in the [bt](http://github.com/staceysern/bt) repo.

### Client Invocation

```
python client.py [file ...]
```
where file is the name of a torrent file

### Browser Control

http://localhost:8080

### Console Invocation

```
python console.py
```

### Console Commands

add [-h] [-n nickname] metainfofile
status [-h] key
quit
