from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Generic, TypeVar

from ..events import Connect, Disconnect, Receive
from ..storage.dict import DictStore


if TYPE_CHECKING:
    from ..servers import AbstractServer


ContentType = TypeVar("ContentType")

logger = logging.getLogger("mara.client")


class AbstractClient(Generic[ContentType]):
    server: AbstractServer
    connected: bool
    read_task: asyncio.Task
    write_task: asyncio.Task
    write_queue: asyncio.Queue
    session: DictStore

    def __init__(self, server: AbstractServer):
        self.server = server
        self.connected = True
        self.session = DictStore()
        # TODO: Queue(maxsize=?) - configure from server
        self.write_queue = asyncio.Queue()

    def __str__(self):
        return "unknown"

    async def read(self) -> ContentType:
        raise NotImplementedError()

    def write(self, data: ContentType):
        """
        Write to the outbound queue
        """
        self.write_queue.put_nowait(data)

    async def flush(self):
        """
        Wait for all outbound data to be sent
        """
        await self.write_queue.join()

    async def _write(self, data: ContentType):
        """
        Write to the connection
        """
        raise NotImplementedError()

    async def close(self):
        logger.info(f"Client {self} closed")
        await self.server.disconnected(self)

    def run(self):
        """
        Add the client read and write tasks to the app's loop
        """
        self.read_task = self.server.app.create_task(self._read_loop())
        self.write_task = self.server.app.create_task(self._write_loop())

    async def _read_loop(self):
        app = self.server.app
        await app.events.trigger(Connect(self))
        logger.info(f"Client {self} connected")
        while self.connected:
            data: ContentType = await self.read()
            if data:
                await app.events.trigger(Receive(self, data))

        logger.info(f"Client {self} disconnected")
        await app.events.trigger(Disconnect(self))

    async def _write_loop(self):
        while self.connected:
            data: ContentType = await self.write_queue.get()
            await self._write(data)
            self.write_queue.task_done()
