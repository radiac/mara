======
Timers
======

Mara has built-in support for timers - for example::

    from mara.timers import PeriodicTimer

    @app.add_timer(PeriodicTimer(every=60))
    async def tick(timer):
        ...


A timer is an instance of an :gitref:`mara/timers/base.py::AbstractTimer` subclass, and
should be attached to the app and a corresponding asynchronous callback function.

Timers run independently of each other within the asyncio loop, so order is not
guaranteed.

Timer instances are actually callable as decorators, so the above is shorthand for::

    async def tick(timer):
        ...

    timer = PeriodicTimer(every=60)
    app.add_timer(timer)
    timer(tick)


API reference
=============

.. autoclass:: mara.timers.periodic.PeriodicTimer
	:members:
