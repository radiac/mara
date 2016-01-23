"""
Server events
"""
from __future__ import unicode_literals

from .base import Event

__all__ = ['Server', 'ListenStart', 'Suspend', 'ListenStop']


class Server(Event):
    "Server event"


class ListenStart(Server):
    "Server listening"

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def __str__(self):
        return "%s on %s:%s" % (
            super(ListenStart, self).__str__(),
            self.host, self.port
        )


class Suspend(Server):
    "Server has been suspended"


class ListenStop(Server):
    "Server is no longer listening"
