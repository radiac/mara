===
API
===


* Also in this section: :doc:`events`, :doc:`storage` and :doc:`contrib`.


.. _class_service:

``cletus.Service``
==================

Central control of the Cletus service.

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
    ``filter``:     A callable which will be used to filter the clients - it
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
    
    @service.listen(cletus.events.Receieve):
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


.. _class_settings:

``cletus.Settings``
===================

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

``cletus.Client``
=================

The client object is the telnet socket manager.


.. _method_client_write:

``write(data)``
---------------

Send the data to the client

Arguments:
:   ``data``:       Raw data received from the client


.. _module_events:

``cletus.events``
=================

See :doc:`events` for details



.. _module_settings:

``cletus.settings``
===================

These are the default settings for any Cletus service.


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

Cletus is primarily designed to be a telnet server for talkers and MUDs, so it
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


.. _setting_store:

``store``
---------

Path to store directory. If it does not exist, it will be created.

Default: ``store``


.. _class_logger:

``cletus.Logger``
=================

To replace the 

.. _method_logger_write:

``write(level, *lines)``
------------------------
Write the lines at the specified level
