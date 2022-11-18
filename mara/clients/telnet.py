from __future__ import annotations

from typing import TYPE_CHECKING

from telnetlib3 import TelnetReader, TelnetWriter

from .base import AbstractClient


if TYPE_CHECKING:
    from ..servers.telnet import TelnetServer


class TelnetClient(AbstractClient[str]):
    reader: TelnetReader
    writer: TelnetWriter
    _str: str | None = None

    def __init__(
        self,
        server: TelnetServer,
        reader: TelnetReader,
        writer: TelnetWriter,
    ):
        super().__init__(server)
        self.reader = reader
        self.writer = writer
        self._str = None

    def __str__(self) -> str:
        # Cache value, it won't be available after connection closes
        if not self._str:
            ip, port = self.writer.get_extra_info("peername")
            self._str = str(ip)
        return self._str

    async def _write(self, data: str):
        # TODO: says it takes bytes but needs str
        self.writer.write(data)  # type: ignore
        await self.writer.drain()
        self._check_is_active()

    def _check_is_active(self):
        if self.reader.at_eof() or self.writer.transport.is_closing():
            self.connected = False

    async def close(self):
        # Close the streams
        self.writer.close()

        # Can't wait to make sure the socket is closed:
        # https://github.com/jquast/telnetlib3/issues/55
        #
        # await self.writer.wait_closed()

        # Terminate the listener loop
        # TODO
        # this.listener_task

        await super().close()

    async def read(self) -> str:
        # TODO: read size and buffers
        data = await self.reader.readline()
        data = data.rstrip("\r\n")
        self._check_is_active()
        return data

    def write(self, data: str, *, end: str = "\r\n"):
        data = f"{data}{end}"
        super().write(data)
