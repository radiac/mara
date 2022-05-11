from __future__ import annotations

import asyncio
import logging
from time import time
from typing import TYPE_CHECKING, Awaitable, Callable


if TYPE_CHECKING:
    from .. import App


logger = logging.getLogger("mara.timer")


class AbstractTimer:
    app: App
    callback: Callable[[AbstractTimer], Awaitable[None]] | None = None
    running: bool = False

    def __str__(self):
        if self.callback is None:
            return str(id(self))
        return self.callback.__name__

    def __call__(
        self, callback: Callable[[AbstractTimer], Awaitable[None]]
    ) -> Callable[[AbstractTimer], Awaitable[None]]:
        logger.debug(f"Timer {self} assigned callback {callback.__name__}")
        self.callback = callback
        return callback

    async def run(self, app: App):
        self.app = app

        logger.debug(f"Timer {self} starting")
        if not self.callback:
            raise ValueError(f"Timer {self} has not been assigned a callback")

        self.running = True
        last_due = time()
        while self.running:
            now = time()
            next_due = self.next_due(last_due, now)
            if not next_due:
                logger.debug(f"Timer {self} at {now} has no next due, stopping")
                break

            logger.debug(f"Timer {self} at {now} is next due {next_due}")
            await asyncio.sleep(next_due - now)
            logger.debug(f"Timer {self} active")
            await self.callback(self)

        self.running = False
        logger.debug(f"Timer {self} stopped")
        # TODO
        # self.app.remove_timer(self)

    def next_due(self, last_due: float, now: float) -> int | float | None:
        """
        Return unix time for the next time the trigger is due

        Arguments:

            last_due (float): when this was last due
            now (float): when this was actually triggered

        Timers using ``now`` for relative calculations will result in drift. Timers
        should ensure that their next due is after ``now``.

        A next due time of 0 or None will terminate the timer
        """
        return 0

    def stop(self):
        logger.debug(f"Timer {self} stopping")
        self.running = False
