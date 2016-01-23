"""
Client events
"""
from __future__ import unicode_literals

from .base import Event

__all__ = ['Client', 'Connect', 'Receive', 'Disconnect']


class Client(Event):
    "Client event"

    def __init__(self, client):
        super(Client, self).__init__()
        self.client = client

    def __str__(self):
        return super(Client, self).__str__().strip() + ' (%s)' % self.client.ip


class Connect(Client):
    "Client connected"


class Disconnect(Client):
    "Client disconnected"


class Receive(Client):
    "Data received"

    def __init__(self, client, data):
        super(Receive, self).__init__(client)
        self.data = data

    def __str__(self):
        return super(Receive, self).__str__().strip() + ': %s' % self.data
