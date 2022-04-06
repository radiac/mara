"""
Client events
"""
from __future__ import annotations

from .base import Event


__all__ = ["Client", "Connect", "Receive", "Disconnect"]


class Client(Event):
    "Client event"

    def __init__(self, client):
        super(Client, self).__init__()
        self.client = client

    def __str__(self):
        msg = super(Client, self).__str__().strip()
        return f"{msg} ({self.client})"


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
        msg = super(Receive, self).__str__().strip()
        return f"{msg}: {self.data}"
