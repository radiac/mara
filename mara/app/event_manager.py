from __future__ import annotations

import logging
from collections import defaultdict
from typing import TYPE_CHECKING, Any

from ..events import Event


if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from .app import App

    # Type aliases
    HandlerType = Callable[[Event], Awaitable[None]]
    FilterType = dict[str, Any]
    EventsType = dict[type[Event], list[tuple[HandlerType, FilterType]]]


logger = logging.getLogger("mara.event")


class EventManager:
    """
    Internal event manager

    Most apps will have one EventManager, created and managed by the App. In normal use
    use the ``App.listen()`` and ``App.trigger()`` methods instead of calling this
    directly.
    """

    app: App

    # Registered events
    events: EventsType

    # Defined event classes
    _known_events: dict[type[Event], None]

    def __init__(self, app: App):
        # Initialise events
        self.app = app
        self.events: EventsType = defaultdict(list)
        self._known_events: dict[type[Event], None] = {}

    def listen(
        self,
        event_class: type[Event],
        handler: HandlerType | None = None,
        **filters: FilterType,
    ):
        """
        Bind a handler callback to the specified event class, and to its subclasses

        Can be called directly::

            manager.listen(Event, handler)
            manager.listen(Event, handler)

        or can be called as a decorator with no handler argument::

            @manager.listen(Event)
            async def callback(event):
                ...

        Arguments:
            event_class (Type[Event]): The Event class to listen for
            handler (Awaitable | None): The handler, if not being decorated
            server (AbstractServer | List[AbstractServer] | None): The Server class or
                classes to filter inbound events
        """
        # Called directly
        if handler is not None:
            self._listen(event_class, handler, filters)
            return handler

        # Called as a decorator
        def decorator(fn):
            self._listen(event_class, fn, filters)
            return fn

        return decorator

    def _listen(
        self,
        event_class: type[Event],
        handler: HandlerType,
        filters: FilterType,
    ):
        """
        Internal method to recursively bind a handler to the specified event
        class and its subclasses. Call listen() instead.
        """
        # Recurse subclasses. Do it before registering for this event in case
        # they're not known yet, then they'll copy handlers for this event
        for subclass in event_class.__subclasses__():
            self._listen(subclass, handler, filters)

        # Register class
        self._ensure_known_event(event_class)
        self.events[event_class].append((handler, filters))

    def _ensure_known_event(self, event_class: type[Event]):
        """
        Ensure the event class is known to the service.

        If it is not, inherit handlers from its first base class
        """
        # If known, nothing to do
        if event_class in self._known_events:
            return

        # If base class isn't an event (ie we're dealing with Event), nothing to do
        base_cls = event_class.__bases__[0]
        if not issubclass(base_cls, Event):
            return

        # We'll know this going forwards, don't want to re-register
        self._known_events[event_class] = None

        # Ensure base class is known - if it isn't, we'll keep working up until we find
        # something we do know
        self._ensure_known_event(base_cls)

        # We've found a known event, propagate down any handlers

        # Propagating at registration means that we don't need to walk the MRO for
        # every event raised
        self.events[event_class] = self.events[base_cls][:]

    async def trigger(self, event: Event):
        """
        Trigger the specified event
        """
        # Make sure we've seen this event class before - will propagate handlers if not
        event_class = type(event)
        self._ensure_known_event(event_class)

        # Make sure all listeners have access to the app, in case they're out of scope
        event.app = self.app

        # Log the event
        logger.info(str(event))
        # self.app.log.event(event)

        # Call all handlers
        handler: HandlerType
        filters: FilterType
        for handler, filters in self.events[event_class]:
            # Catch stopped event
            if event.stopped:
                return

            # Filter anything which doesn't match
            # TODO: This could be enhanced to allow more complex filtering rules
            if not all(
                hasattr(event, filter_key)
                and getattr(event, filter_key) == filter_value
                for filter_key, filter_value in filters.items()
            ):
                return

            # Pass to the handler
            await handler(event)
