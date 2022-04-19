from __future__ import annotations

import asyncio
import logging

from ..clients.socket import SocketClient, SocketMixin, TextClient
from ..constants import DEFAULT_HOST, DEFAULT_PORT
from .base import AbstractAsyncioServer


logger = logging.getLogger("mara.server")


class AbstractSocketServer(AbstractAsyncioServer):
    client_class: type[SocketMixin]
    _host: str
    _port: int

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        self.host = host
        self.port = port
        super().__init__()

    def __str__(self):
        return f"Socket {self.host}:{self.port}"

    async def create(self):
        await super().create()

        self.server = await asyncio.start_server(
            client_connected_cb=self.handle_connect,
            host=self.host,
            port=self.port,
        )

    async def handle_connect(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        client: SocketMixin = self.client_class(
            server=self, reader=reader, writer=writer
        )
        await self.connected(client)


class SocketServer(AbstractSocketServer):
    client_class: type[SocketClient] = SocketClient


class TextServer(AbstractSocketServer):
    client_class: type[TextClient] = TextClient
