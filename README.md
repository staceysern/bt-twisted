BitTorrent
===============

A BitTorrent client written in Python.

This version of the BitTorrent client consists of the client itself as well as a console for user control.  It can also be controlled with a javascript application in a browser.  It implements downloading but not uploading.  It can handle multiple torrents at a time but does not manage traffic load.  It uses a very simple strategy for determining which blocks to request and does not implement keep alives, pipelined requests or endgame strategy.  

Client Invocation
-----------------

python client.py [metainfofile ...]   

Browser Control
---------------

http://localhost:8080

Console Invocation
------------------

python console.py

Console Commands
----------------

add [-h] [-n nickname] metainfofile  
status [-h] key  
quit  

