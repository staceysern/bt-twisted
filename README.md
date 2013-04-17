BitTorrent
===============

A BitTorrent client written in Python.

This version of the client implements downloading but not uploading.  It can handle multiple torrents at a time but does not manage traffic load.  It uses a very simple strategy for determining which blocks to request and does not implement keep alives, pipelined requests or endgame strategy.  

Invocation
----------

python client.py 

Unit Tests
----------

py.test is used for unit testing.  From the test directory run: 

PYTHONPATH=..:${PYTHONPATH} py.test



