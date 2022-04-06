"""
Mara events
"""
from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from ..app import App


class Event(object):
    """
    Non-specific event

    All events are derived from this class.
    """

    app: App | None

    def __init__(self):
        self.stopped = False

        # App will be added by event handler
        self.app = None

    def stop(self):
        """
        Stop the event from being passed to any more handlers
        """
        self.stopped = True

    def __str__(self):
        """
        Return this event as a string
        """
        label = getattr(self.__class__, "hint", self.__class__.__doc__ or "")
        label = (label.strip().splitlines()[0],)
        return f"[{self.__class__.__name__}]: {label}"
