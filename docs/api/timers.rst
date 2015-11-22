======
Timers
======

.. _timer_registry:

Timer registry
==============

Timers are held and triggered by the timer registry for each service (on the
attribute ``service.timers``.

It is recommended that you don't interact with the registry directly - instead,
you should use the :ref:`service.timer <method_service_timer>` method to
decorate your :ref:`timer handler <timer_handlers>`.

That said it is possible to add a new timer directly by calling the ``add``
method on the registry, ie ``service.timers.add(timer)``. This can be useful
if binding a custom timer class which defines its own handler - see
:ref:`timer_handlers` for an example.

Once a timer is registered, the service is then responsible for triggering any
due (or overdue) timers at every poll, at a frequency of roughly 1/10th of a
second by default (controlled by the ``socket_activity_timeout`` setting,
delayed by any event processing).

Timers are stored in a linked list in the order that they are due. The
registry holds a reference to the first timer in the list (as the ``next``
attribute), then each timer holds a reference to the next one (again, as the
``next`` attribute).


.. _timer_handlers:

Timer handlers
==============

Timer handlers are the functions called when the timer is triggered. In all the
built-in timers, handlers are functions assigned to an instantiated timer's
``fn`` attribute. They are passed a single argument: ``timer``, the timer
instance they are assigned to. This allows the timer to be modified by the
handler - see :ref:`timer_classes` for more details.

An alternative approach to defining a timer handler is to define a custom timer
class, and override the ``trigger`` function. This would be a useful approach
if you wanted to have multiple timers using the same handler - for example, you
could create a subclass of :ref:`DateTimer <class_timers_date_datetimer>` which
takes a user and date in the constructor, then calls the same handler to wish
the user happy birthday on the specified date. With this approach you would
add the timer instances to the registry directly - see :ref:`timer_registry`
for details.


.. _timer_classes:

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

``mara.timers.Timer``
---------------------

Base class for timer classes. It is more likely that the other timer classes
will be more useful in your code.

Arguments:
    ``due``
        The timestamp that the event is due
    ``context``
        Optional context


.. _class_timers_periodtimer:

``mara.timers.PeriodTimer``
---------------------------

This repeats after the specified period (in seconds).

It is the default class for the service decorator :ref:`method_service_timer`.

Arguments:
    ``period``
        The number of seconds until it is due
    ``context``
        Optional context

Example of a periodic announcement::

    from mara import timers
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
    
    from mara import timers
    @service.listen(events.Receive)
    def delayed_echo(event):
        timer = timers.PeriodTimer(period=3, context=event)
        timer.fn = do_echo
        service.timers.add(timer)


.. _class_timers_randomtimer:

``mara.timers.RandomTimer``
---------------------------

This repeats after a random amount of time, between a specified minimum and
maximum period (in seconds)

Arguments:

    min_period
        The number of seconds until it is due
    context
        Optional context

Example of a periodic announcement, every 1 to 3 minutes::

    from mara import timers
    @service.timer(timers.RandomTimer, min_period=1*60, max_period=3*60)
    def every_so_often(timer):
        service.write_all('You are wasting your life.')


.. _class_timers_date_datetimer:

``mara.timers.date.DateTimer``
------------------------------

This timer repeats at a specified date or time.

It is defined in a separate module to the others because it depends on the
module ``dateutil`` - if not installed, it will raise an ImportError. To
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

    ``year``
        The year the timer will trigger (None for every year)
    ``month``
        The month the timer will trigger (None for every month)
    ``day``
        The day the timer will trigger (None for every day)
    ``hour``
        The hour the timer will trigger (None for every hour)
    ``minute``
        The minute the timer will trigger (None for every minute)
    ``second``
        The second the timer will trigger (None for every second)
    ``context``
        Optional context

Because the calculation of the next due date is more intensive than that of
other timers, you should probably think carefully before setting
``second=None``, and consider using a more appropriate timer instead
- or a combination of a ``DateTimer`` which adds a new ``PeriodTimer``.

Example of an announcement at a specific date and time::

    from mara.timers.time import DateTimer
    @service.timer(DateTimer, month=3, day=1, hour=12)
    def happy_birthday(timer):
        service.write_all("Happy Birthday to Radiac! He is wasting his life.")
