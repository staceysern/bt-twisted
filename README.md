BitTorrent
===============

A BitTorrent client written in Python.

This version of the client implements downloading but not uploading.  It can handle multiple torrents at a time but does not manage traffic load.  It uses a very simple strategy for determining which blocks to request and does not implement pipelined requests or endgame strategy.  

Requirements
------------

bencode   
bitstring  
requests  

Invocation
----------

python client.py 



