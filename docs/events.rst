======
Events
======


.. _event_handlers:

Event Handlers
==============

An event handler is an ``async`` function which you define and register with the app to
handle certain classes of events. It is passed the instance of the event, and handlers
are able to modify it for future handlers if they wish.

For example::

    @app.listen(events.Receive)
    async def echo(event: events.Receive):
        event.client.write(event.data)


Multiple handlers can listen to a single event; they will be called in the order they
are defined. If a handler does not want later handlers to receive the event, it can call
``event.stop()``.

Events also are bubbled up to superclass handlers  - see :ref:`event_inheritance` for
more details.


.. _event_inheritance:

Event inheritance
=================

It is often desirable to bind a handler to listen to a category of events; for
example, if you want to extend all client events by adding a user attribute.

To make this easy, Mara lets you bind a handler to an event base class. For
example, a handler bound to ``events.Client`` will also be called for
``Receive``, ``Connect`` and ``Disconnect`` events.

The order that handlers are bound is still respected.


Writing custom events
=====================

Create a subclass of ``mara.events.Event`` and ensure it sets a docstring
or ``__str__`` for logging.

Handlers are matched by comparing classes, so you can have two classes with the
same name (as long as they are in separate modules).


API reference
=============

.. autoclass:: mara.events.Event
	:members:
