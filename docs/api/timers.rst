======
Timers
======

Timer registry
==============

Timers are held and triggered by the timer registry.

To add a new timer to the registry, call ``add(timer)``. The service is then
responsible for triggering any due (or overdue) timers at every poll, normally
at a frequency of roughly 1/10th of a second (controlled by the
``socket_activity_timeout`` setting, delayed by any event processing).

Timers are stored in a linked list in the order that they are due. The
registry holds a reference to the first timer in the list (as the ``next``
attribute), then each timer holds a reference to the next one (again, as the
``next`` attribute).


Timer classes
=============

Timers have an ``update`` method which set their ``due`` attribute - the
timestamp that they are due to be triggered. When triggered, the ``trigger``
method is called.

All timer classes also take a ``context`` argument, so data can be passed in
to the trigger function, or values persisted across calls.

The trigger function can stop the timer from being triggered again in the
future by calling ``timer.stop()`` (or changing ``timer.active`` to ``False``).


.. _class_timers_timer:

``cletus.timers.Timer``
-----------------------

Base class for timer classes. It is more likely that the other timer classes
will be more useful in your code.

Arguments:

:   due:        The timestamp that the event is due
    context:    Optional context


.. _class_timers_periodtimer:

``cletus.timers.PeriodTimer``
-----------------------------

This repeats after the specified period (in seconds).

It is the default class for the service decorator :ref:`method_service_timer`.

Arguments:

:   period:     The number of seconds until it is due
    context:    Optional context

Example of a periodic announcement::

    from cletus import timers
    @service.timer(timers.PeriodTimer, period=60)
    def every_minute(timer):
        service.write_all('You have wasted another minute of your life.')

Example of a delay::
    
    # Echo client with a 3 second delay
    
    def do_echo(timer):
        event = timer.context
        event.client.write(event.data)
        # Only fire once
        timer.stop()
    
    from cletus import timers
    @service.listen(events.Receive)
    def delayed_echo(event):
        timer = timers.PeriodTimer(period=3, context=event)
        timer.fn = do_echo
        service.timers.add(timer)


.. _class_timers_randomtimer:

``cletus.timers.RandomTimer``
-----------------------------

This repeats after a random amount of time, between a specified minimum and
maximum period (in seconds)

Arguments:

:   min_period: The number of seconds until it is due
    context:    Optional context

Example of a periodic announcement, every 1 to 3 minutes::

    from cletus import timers
    @service.timer(timers.RandomTimer, min_period=1*60, max_period=3*60)
    def every_so_often(timer):
        service.write_all('You are wasting your life.')


.. _class_timers_time_datetimer:

``cletus.timers.time.DateTimer``
--------------------------------

This timer repeats at a specified date or time.

It is defined in a separate module to the others because it depends on the
module ``dateutil`` - if not installed, it will raise an ImportError. to
install ``dateutil``, use ``pip install python-dateutil``.

It takes keyword arguments describing the date and time; if a value is None,
when the timer updates it will use the non-None values to give the soonest
date and time; eg to fire at 2pm on the 1st of each month::

    timer = DateTimer(day=1, hour=14)

The defaults provide the value ``0`` for ``minute`` and ``second``, and
``None`` for the others, meaning that by default it will fire at the start of
every hour.

It is not timezone aware.

Arguments:

:   year:       The year the timer will trigger (None for every year)
    month:      The month the timer will trigger (None for every month)
    day:        The day the timer will trigger (None for every day)
    hour:       The hour the timer will trigger (None for every hour)
    minute:     The minute the timer will trigger (None for every minute)
    second:     The second the timer will trigger (None for every second)
    context:    Optional context

Because the calculation of the next due date is more intensive than that of
other timers, you should probably think carefully before setting
``second=None``, and consider using a more appropriate timer instead
- or a combination of a ``DateTimer`` which adds a new ``PeriodTimer``.

Example of an announcement at a specific date and time::

    from cletus.timers.time import DateTimer
    @service.timer(DateTimer, month=3, day=1, hour=12)
    def happy_birthday(timer):
        service.write_all("Happy Birthday to Radiac! He is wasting his life.")
