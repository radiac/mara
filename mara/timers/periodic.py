from __future__ import annotations

from .base import AbstractTimer


class PeriodicTimer(AbstractTimer):
    every: int | float
    strict: bool

    def __init__(self, every: int | float, strict=False):
        super().__init__()
        self.every = every
        self.strict = strict

    def next_due(self, last_due: float, now: float) -> int | float:
        """
        Return unix time for the next time the trigger is due
        """
        if self.strict:
            next = last_due + self.every

        else:
            next = last_due

        if next <= now:
            next = now + self.every

        return next
