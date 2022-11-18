from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Coroutine, List

from ..events import Event, PostStart, PostStop, PreStart, PreStop
from ..status import Status
from . import event_manager
from .logging import configure as configure_logging


if TYPE_CHECKING:
    from ..servers import AbstractServer
    from ..timers import AbstractTimer

configure_logging()
logger = logging.getLogger("mara.app")


class App:
    """
    Orchestrate servers, clients and tasks
    """

    loop: asyncio.AbstractEventLoop | None = None
    servers: List[AbstractServer]
    events: event_manager.EventManager
    timers: List[AbstractTimer]
    _status: Status = Status.IDLE

    def __init__(self):
        self.servers = []
        # TODO: move clients to server
        self.clients = []
        self.timers = []

        self.events = event_manager.EventManager(self)

    def add_server(self, server: AbstractServer) -> AbstractServer:
        """
        Add a new Server instance to the async loop

        The server will start listening when the app is ``run()``. If it is already
        running, it will start listening immediately.
        """
        logger.debug(f"Add server {server}")
        self.servers.append(server)

        if self.loop:
            logger.debug(f"Running server {server}")
            self.create_task(server.run(self))

        return server

    def remove_server(self, server: AbstractServer):
        """
        Stop and remove the specified Server instance
        """
        if server.status == Status.RUNNING:
            logger.debug(f"Stopping server {server}")
            server.stop()

        logger.debug(f"Removing server {server}")
        self.servers.remove(server)

    def add_timer(self, timer: AbstractTimer) -> AbstractTimer:
        """
        Add a new Timer instance to the async loop

        The timer will start when the app is ``run()``. If it is already running, it
        will start immediately.

        Returns the timer instance. Because timer instances are callable decorators, you
        can use this as a decorator to define a timer and its function in one::

            @app.add_timer(PeriodicTimer(every=1))
            async def tick(timer):
                ...

        which is shorthand for::

            async def tick(timer):
                ...

            timer = PeriodicTimer(every=60)
            app.add_timer(timer)
            timer(tick)
        """
        logger.debug(f"Add timer {timer}")
        self.timers.append(timer)

        if self.loop:
            logger.debug(f"Timer {timer} starting")
            self.create_task(timer.run(self))
            logger.debug(f"Timer {timer} stopped")

            # TODO: extend self.create_task to callback to a fn to clean up self.timers

        return timer

    def run(self, debug=True):
        """
        Start the main app async loop

        This will start any Servers which have been added with ``add_server()``
        """
        self._status = Status.STARTING

        # TODO: Should add some more logic around here from asyncio.run
        self.loop = loop = asyncio.new_event_loop()
        logger.debug("Loop starting")
        loop.run_until_complete(self.events.trigger(PreStart()))

        for server in self.servers:
            self.create_task(server.run(self))

        for timer in self.timers:
            self.create_task(timer.run(self))

        logger.debug("Loop running")
        self._status = Status.RUNNING
        loop.run_until_complete(self.events.trigger(PostStart()))
        try:
            loop.run_forever()
        finally:
            logger.debug("Loop stopping")
            self._status = Status.STOPPING
            loop.run_until_complete(self.events.trigger(PreStop()))
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
            self._status = Status.STOPPED
            self.loop = None
            logger.debug("Loop stopped")

            # Loop has terminated
            asyncio.run(self.events.trigger(PostStop()))

    def create_task(self, task_fn: Coroutine[Any, Any, Any]):
        if self.loop is None:
            # TODO: Handle pending tasks here
            raise ValueError("Loop is not running")
        task = self.loop.create_task(task_fn)
        task.add_done_callback(self._handle_task_complete)
        return task

    def _handle_task_complete(self, task: asyncio.Task):
        try:
            task.result()
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Task failed")

    def listen(
        self,
        event_class: type[Event],
        handler: event_manager.HandlerType | None = None,
        **filters: event_manager.FilterType,
    ):
        """
        Bind a handler callback to the specified event class, and to its subclasses

        Arguments:

            event_class (Type[Event]): The Event class to listen for
            handler (Awaitable | None): The handler, if not being decorated
            **filters: Key value pairs to match against inbound events

        Can be called directly::

            app.listen(Event, handler)

        or can be called as a decorator with no handler argument::

            @app.listen(Event)
            async def callback(event):
                ...
        """
        return self.events.listen(event_class, handler, **filters)

    @property
    def status(self):
        """
        Get the status of the app and its servers

        Difference between this and self._status is when the app loop is RUNNING, this
        will return STARTING until all servers are listening
        """
        if not self._status == Status.RUNNING:
            return self._status

        if all([server.status == Status.RUNNING for server in self.servers]):
            return Status.RUNNING
        return Status.STARTING

    def stop(self):
        """
        This will ask the main loop to stop, shutting down all servers, connections and
        other async tasks.
        """
        if self.loop:
            logger.debug("Stopping servers")
            for server in self.servers:
                server.stop()

            logger.debug("Requesting loop stop")
            self.loop.stop()
