from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from ..clients.socket import SocketClient, SocketMixin, TextClient
from ..events import ListenStart, ListenStop
from ..status import Status
from .base import AbstractServer


if TYPE_CHECKING:
    from ..app import App

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9000

logger = logging.getLogger("mara.server")


class AbstractSocketServer(AbstractServer):
    server: asyncio.base_events.Server
    client_class: type[SocketMixin]
    _host: str
    _port: int

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        self.host = host
        self.port = port
        super().__init__()

    def __str__(self):
        return f"Socket {self.host}:{self.port}"

    async def create(self, app: App):
        await super().create(app)

        logger.debug(f"Server starting: {self}")
        self.server = await asyncio.start_server(
            self.handle_connect, self.host, self.port
        )
        logger.debug(f"Server started: {self}")

    async def listen(self):
        await super().listen()

        # Raise the event
        logger.info(f"Server listening: {self}")
        await self.app.events.trigger(ListenStart(self))

        # Main server loop
        async with self.server:
            await self.server.serve_forever()

        # Look has exited, likely due to a call to self.stop()
        logger.debug(f"Server stopping: {self}")
        await self.app.events.trigger(ListenStop(self))
        logger.info(f"Server stopped: {self}")
        self._status = Status.STOPPED

    async def handle_connect(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        client: SocketMixin = self.client_class(
            server=self, reader=reader, writer=writer
        )
        await self.connected(client)

    def stop(self):
        """
        Shut down the server
        """
        self._status = Status.STOPPING
        logger.info(f"Server closing: {self}")
        self.server.close()

        # No call to super - self._status is set to STOPPED by listen()

    @property
    def status(self) -> Status:
        status = super().status

        if status == Status.RUNNING and not self.server.is_serving():
            return Status.STARTING

        return status


class SocketServer(AbstractSocketServer):
    client_class: type[SocketClient] = SocketClient


class TextServer(AbstractSocketServer):
    client_class: type[TextClient] = TextClient
