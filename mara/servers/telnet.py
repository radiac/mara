"""
Telnet server

Wrapper around telnetlib3, https://pypi.org/project/telnetlib3/
"""
from __future__ import annotations

from telnetlib3 import TelnetReader, TelnetWriter

from ..clients.telnet import TelnetClient
from ..constants import DEFAULT_HOST, DEFAULT_PORT
from .base import AbstractAsyncioServer


try:
    import telnetlib3
except ImportError:
    raise ValueError("telnetlib3 not found - pip install mara[telnet]")


class TelnetServer(AbstractAsyncioServer):
    client_class: type[TelnetClient] = TelnetClient

    def __init__(
        self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, **telnet_kwargs
    ):
        self.host = host
        self.port = port

        if "shell" in telnet_kwargs:
            raise ValueError("Cannot specify a shell for TelnetServer")
        self.telnet_kwargs = telnet_kwargs
        self.telnet_kwargs["shell"] = self.handle_connect

        super().__init__()

    def __str__(self):
        return f"Telnet {self.host}:{self.port}"

    async def create(self):
        await super().create()
        loop = self.app.loop
        if loop is None:
            raise ValueError("Cannot start TelnetServer without running loop")

        self.server = await loop.create_server(
            protocol_factory=lambda: telnetlib3.TelnetServer(**self.telnet_kwargs),
            host=self.host,
            port=self.port,
        )

    async def handle_connect(self, reader: TelnetReader, writer: TelnetWriter):
        client: TelnetClient = self.client_class(
            server=self, reader=reader, writer=writer
        )
        await self.connected(client)
