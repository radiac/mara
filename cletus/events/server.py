"""
Server events
"""
from .base import Event

__all__ = ['ListenStart', 'Suspend', 'ListenStop']

class ListenStart(Event):
    "Server listening"
    def __init__(self, host, port):
        self.host = host
        self.port = port
    def __str__(self):
        return "%s on %s:%s" % (
            super(ListenStart, self).__str__(),
            self.host, self.port
        )
    
class Suspend(Event):       "Server has been suspended"
class ListenStop(Event):    "Server is no longer listening"
