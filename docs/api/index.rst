===
API
===


Also in this section:

.. toctree::
    :maxdepth: 2

    events
    timers
    storage
    contrib


.. _class_service:

``mara.Service``
================

Central control of the Mara service.

.. _method_service_run:

``run(*args, **kwargs)``
------------------------

Build settings and run the service.

Arguments:

:   ``*args``:      List of settings sources - see :ref:`settings` for options
    ``**kwargs``:   Settings


.. _method_service_listen:

``listen(event_class, handler)``
--------------------------------

Bind a function to a class of event.

Can be used as a direct call, or as a decorator::

    service.listen(Event, handler)
    
    @service.listen(Event):
    def handler(event):
        pass

Arguments:

:   ``Event``:      An :ref:`class_events_event` subclass (not an instance)
    ``handler``:    A reference to a handler. Omit this argument if you are
                    using ``listen`` as a decorator. See :ref:`event_handlers`
                    for details.

.. _method_service_trigger:

``trigger(event)``
------------------

Trigger an event.

Arguments:

:   ``event``:      An instance of an :ref:`class_events_event` subclass 


.. _method_service_timer:

``timer(cls=PeriodTimer, **kwargs)``
------------------------------------

Function decorator to define a timer class instance. The default class is
``PeriodTimer``; keyword arguments are passed to the timer class constructor,
and the timer's ``fn`` attribute is set to the decorated function. When
triggered, the decorated function is passed the timer class instance.

For example::

    @service.timer(period=60)
    def every_minute(timer):
        service.write_all('Another minute has passed')

Here the decorator is shorthand for::

    from mara import timers
    timer = timers.PeriodTimer(period=60)
    timer.fn = every_minute
    service.timers.add(timer)

You can use a different timer class by passing it as the first argument,
``cls``::

    from mara.timers import PeriodTimer
    @service.timer(PeriodTimer, period=60)
    def every_minute(timer):
        service.write_all('Time passes')

See :doc:`timers` for details of built-in timer classes, and writing your own.


.. _method_service_write:

``write(clients, *data)``
-------------------------

Send the data to the specified clients.

Arguments:

:   ``clients``:    A :ref:`class_client` instance, or list of ``Client``
                    instances.
    ``*data``:      One or more lines of data to send to the client.
                    Should not contain newline sequences.


.. _method_service_write_all:

``write_all(*data, **kwargs)``
------------------------------

Send the data to all connected clients.

Arguments:

:   ``*data``:      One or more lines of data to send to the client.
                    Should not contain newline sequences.

Optional keyword arguments:

:   ``filter``:     A callable which will be used to filter the clients - it
                    will be passed the same arguments as a
                    :ref:`global filter <attr_service_filter_all>`
    ``exclude``:    A :ref:`class_client` instance, or list of ``Client``
                    instances.
    other:          Any other keyword arguments will be passed to the filters.


.. _attr_service_filter_all:

``filter_all = callable``
-------------------------

Set a filter for all :ref:`write_all <method_service_write_all>` calls. This
can be supplemented by the ``filter`` keyword argument - both can use the
same callables.

The callable that you assign should expect the following arguments:

:   ``service``:    The service that is in the process of writing the data
    ``clients``:    A list of :ref:`class_client` instances
    ``**kwargs``:   The keyword arguments passed to ``write_all`` (except
                    ``filter`` and ``exclude``).

It should then return a filtered list of clients.

If the callable is set to None, the filter will be reset and no filtering will
be performed.

For example:
    
    # Only write to every other client
    service.filter_all = lambda service, clients: clients[::2]

or slightly more complex:

    def room_filter(service, clients, room=None):
        if not room:
            return []
        return [c for c in clients if c in room.clients]
    
    # We could set this as a global filter with:
    #   service.filter_all = room_filter
    # But this would stop us from broadcasting global events
    
    @service.listen(mara.events.Receieve):
    def chat(event):
        client.write('You say %s' % event.data)
        service.write_all(
            '%s says: %s' % (event.client.username, event.data),
            except=event.client,
            # So we'll pass it in the write_all call
            filter=room_filter,
            room=event.client.room,
        )


.. _method_service_store:

``store(cls, name)``
--------------------

Retrieve the store instance of the given class and name.

See :ref:`storage` for more details of how storage works.


.. _method_service_restart:

``restart()``
-------------

Restarts the process while maintaining the service state and client sockets.
Only available when the process is run using the :ref:`angel <angel>`.

When called, the current service will do the following:

#. ``service.restart()`` is called
#. If we don't have an angel, raise a ``ValueError``
#. Trigger :ref:`PreRestart <events_service>` event
#. Flush all client output buffers (so they can see a restart notification)
#. Suspend the server (do no further socket processing)
#. Serialise the service state and client sockets
#. Pass the serialised data to the angel
#. Wait for a response from the angel

The angel will then:

#. Receive serialised data from the current process
#. Start a new process

The new process will then:

#. Connect to the angel
#. Trigger :ref:`PreStart <events_service>` event
#. Request serialised data
#. Deserialise the data into the new service
#. Notify the angel that it has started
#. Trigger :ref:`PostStart <events_service>` event
#. Trigger :ref:`PostRestart <events_service>` event

When the angel receives notification that the new process has started, it will
tell the old process that everything is ok. The old process will then terminate
immediately.

.. note::

    There is currently no support for restarting multiple services in the same
    process.


.. _class_settings:

``mara.Settings``
=================

A container for service settings.

Additional custom settings can be stored on the ``Settings`` class, but do not
start them with an underscore, and make sure they do not start with an
underscore, and that they do not clash with methods on the ``Settings`` class.
You should use a prefix to ensure they do not collide with any other settings;
eg: ``myproject_mysetting=20``.

.. _method_settings_load:

``load(source)``
----------------

Load a settings source and override existing settings

If called from code rather than the command line you can also pass a reference
to an imported module::

    import myproject.settings
    settings.load(myproject.settings)
    # Equivalent to:
    settings.load('module:myproject.settings')


.. _class_client:

``mara.Client``
===============

The client object is the telnet socket manager.


.. _method_client_write:

``write(data)``
---------------

Send the data to the client

Arguments:
:   ``data``:       Raw data received from the client


.. _module_events:

``mara.events``
=================

See :doc:`events` for details



.. _module_settings:

``mara.settings.defaults``
==========================

These are the default settings for any Mara service. Look at this file for
details of all settings; the important ones are:


``host``
--------
Host IP to bind to

Default: ``127.0.0.1``


``port``
--------
Port to bind to

Default: ``9000``


.. _setting_socket_raw:

``socket_raw``
--------------
Raw socket mode

Mara is primarily designed to be a telnet server for talkers and MUDs, so it
normally treats inbound and outbound data as telnet content - performing
telnet negotiation, breaking and joining raw socket data with newlines.
However, this can be disabled using this setting, so you can read and write the
raw data.

If ``True``, disable telnet negotiation, do not buffer or strip inbound data,
and do not modify outbound data.

If ``False``, assume this is a telnet connection using ``\r\n`` for line feeds.
This will enable telnet negotiation, buffer inbound data until the newline
sequence is received (which will be stripped), and use the newline sequence to
suffix all lines of outbound data.

Default: ``False``


.. _setting_root_path:

``root_path``
-------------

This is an optional root path for all non-absolute path settings. If it is
set to None, the directory containing the service script will be used.
Individual path settings will ignore this if they are absolute themselves.

Default: ``None`` (use script directory)

.. _setting_store:

``store_path``
--------------

Path to store directory. If it does not exist, it will be created.

If it is not an absolute path, Mara will use the root_path setting.

Default: ``store``


.. _class_logger:

``mara.Logger``
===============

To replace the 

.. _method_logger_write:

``write(level, *lines)``
------------------------
Write the lines at the specified level
