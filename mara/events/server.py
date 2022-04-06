"""
Server events
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from .base import Event


__all__ = ["Server", "ListenStart", "Suspend", "ListenStop"]


if TYPE_CHECKING:
    from ..servers import AbstractServer


class Server(Event):
    "Server event"
    server: AbstractServer

    def __init__(self, server: AbstractServer):
        self.server = server

    def __str__(self) -> str:
        return f"{super().__str__()}: {self.server}"


class ListenStart(Server):
    "Server listening"


class Suspend(Server):
    "Server has been suspended"


class ListenStop(Server):
    "Server is no longer listening"
