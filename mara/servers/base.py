from __future__ import annotations

import logging
from typing import TYPE_CHECKING

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

    async def connected(self, client: AbstractClient):
        """
        Register a new client connection and start the client lifecycle
        """
        logger.info(f"Connection from {client}")
        self.clients.append(client)
        client.run()

    def stop(self):
        """
        Shut down the server
        """
        self._status = Status.STOPPED

    @property
    def status(self) -> Status:
        return self._status
