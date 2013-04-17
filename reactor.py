"""
The Reactor synchronously dispatches service requests received concurrently
from multiple resources to event handlers.  The Reactor is a singleton
object which runs an event loop which blocks until one of the resources it is
monitoring is ready to be serviced.  It monitors file objects (including
sockets).  Event handlers register with the Reactor to be notified on read
and/or write events for a particular resource.  When no longer interested,
they may unregister the resource.  Event handlers may also register a timer to
be notified after an interval of time has passed.

A handler registering to receive read events must implement a read_event()
method on which to be called when a read event occurs and a stream() method
which returns a reference to the resource to be monitored.  Similarly, a
handler for write events must implement a write_event() and a stream() method.
A handler registering to receive a timer notification must implement a
timer_event() method.
"""

import bisect
import logging
import select
import time
from decorators import singleton

logger = logging.getLogger('bt.reactor')


@singleton
class Reactor(object):
    def __init__(self):
        self._read_handlers = {}
        self._write_handlers = {}
        self._timer_handlers = []
        self._timer_id = 0

    def register_for_read_events(self, handler):
        self._read_handlers[handler.stream()] = handler

    def register_for_write_events(self, handler):
        self._write_handlers[handler.stream()] = handler

    def unregister_for_read_events(self, handler):
        if handler.stream() in self._read_handlers:
            del self._read_handlers[handler.stream()]

    def unregister_for_write_events(self, handler):
        if handler.stream() in self._write_handlers:
            del self._write_handlers[handler.stream()]

    def schedule_timer(self, interval, handler):
        self._timer_id += 1
        bisect.insort(self._timer_handlers, (time.time()+interval, handler,
                      self._timer_id))
        return self._timer_id

    def cancel_timer(self, timer_id):
        self._timer_handlers = [(timeout, handler, t)
                                for (timeout, handler, t)
                                in self._timer_handlers if t != timer_id]

    def run(self):
        while True:
            now = time.time()
            unexpired = 0
            for i, (timeout, handler, _) in enumerate(self._timer_handlers):
                if timeout < now:
                    handler.timer_event()
                    unexpired = i+1
                else:
                    unexpired = i
                    break
            self._timer_handlers = self._timer_handlers[unexpired:]

            readable, writable, _ = select.select(self._read_handlers.keys(),
                                                  self._write_handlers.keys(),
                                                  [], 0.001)

            for stream in readable:
                if stream in self._read_handlers.keys():
                    self._read_handlers[stream].read_event()

            for stream in writable:
                if stream in self._write_handlers.keys():
                    self._write_handlers[stream].write_event()
