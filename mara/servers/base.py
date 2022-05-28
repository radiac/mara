from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from ..events import ListenStart, ListenStop
from ..status import Status


if TYPE_CHECKING:
    from ..app import App
    from ..clients import AbstractClient

logger = logging.getLogger("mara.server")


class AbstractServer:
    app: App
    clients: list[AbstractClient]
    _status: Status = Status.IDLE

    def __init__(self):
        self.clients = []

    def __str__(self):
        return "AbstractServer"

    async def run(self, app: App):
        """
        Create the server
        """
        self.app = app
        await self.create()
        await self.listen()

    async def create(self):
        logger.debug(f"Server starting: {self}")
        self._status = Status.STARTING

    async def listen(self):
        """
        Main listening loop
        """
        logger.debug(f"Server running: {self}")
        self._status = Status.RUNNING

        # Raise the event
        await self.app.events.trigger(ListenStart(self))

        # Start the server
        await self.listen_loop()

        # Look has exited, likely due to a call to self.stop()
        logger.debug(f"Server stopping: {self}")
        await self.app.events.trigger(ListenStop(self))
        logger.info(f"Server stopped: {self}")
        self._status = Status.STOPPED

    async def listen_loop(self):
        """
        Placeholder for subclasses to implement their listen loop
        """
        pass

    async def connected(self, client: AbstractClient):
        """
        Register a new client connection and start the client lifecycle
        """
        logger.info(f"Connection from {client}")
        self.clients.append(client)
        client.run()

    async def disconnected(self, client: AbstractClient):
        """
        Unregister a client who has disconnected
        """
        self.clients.remove(client)

    def stop(self):
        """
        Shut down the server
        """
        self._status = Status.STOPPING
        logger.info(f"Server closing: {self}")

    @property
    def status(self) -> Status:
        return self._status


class AbstractAsyncioServer(AbstractServer):
    """
    Base class for servers based on asyncio.Server
    """

    server: asyncio.base_events.Server

    async def listen_loop(self):
        async with self.server:
            await self.server.serve_forever()

    def stop(self):
        """
        Shut down the server
        """
        super().stop()
        self.server.close()

    @property
    def status(self) -> Status:
        status = super().status

        if status == Status.RUNNING and not self.server.is_serving():
            return Status.STARTING

        return status
