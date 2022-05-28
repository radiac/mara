from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Protocol

from .base import AbstractClient


if TYPE_CHECKING:
    from ..servers import AbstractServer


class ClientCanStream(Protocol):

    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter

    def __init__(
        self,
        server: AbstractServer,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ):
        ...


class SocketMixin(AbstractClient):
    """
    Mixin for any client class which uses byte sockets
    """

    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter

    def __init__(
        self,
        server: AbstractServer,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ):
        super().__init__(server)
        self.reader = reader
        self.writer = writer

    def __str__(self) -> str:
        ip, port = self.writer.get_extra_info("peername")
        return str(ip)

    async def _write(self, data: bytes):
        self.writer.write(data)
        await self.writer.drain()
        self._check_is_active()

    def _check_is_active(self):
        if self.reader.at_eof() or self.writer.transport.is_closing():
            self.connected = False

    async def close(self):
        # Close the streams
        self.writer.close()
        await self.writer.wait_closed()

        # Terminate the listener loop
        # TODO
        # this.listener_task

        await super().close()


class SocketClient(SocketMixin, AbstractClient[bytes]):
    """
    Read and write bytes
    """

    async def read(self) -> bytes:
        # TODO: read size and buffers
        data = await self.reader.read(1024)
        self._check_is_active()
        return data


class TextClient(SocketMixin, AbstractClient[str]):
    """
    Read and write unicode over an underlying byte socket
    """

    async def read(self) -> str:
        # TODO: read size and buffers
        try:
            data: bytes = await self.reader.readuntil(b"\r\n")
        except asyncio.exceptions.IncompleteReadError:
            self.connected = False
            return ""
        data = data.rstrip(b"\r\n")
        self._check_is_active()
        text: str = data.decode()
        return text

    def write(self, data: str, *, end: str = "\r\n"):
        raw_data: bytes = f"{data}{end}".encode()
        super().write(raw_data)
