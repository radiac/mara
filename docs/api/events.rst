======
Events
======

.. _class_events_event:

``cletus.events.Event``
=======================

Base class for event classes.

Events are containers for event data; event attributes are passed as keyword
arguments to the constructor. For example::

    event = cletus.events.Receive(client=client_obj, data=raw_input)

Events can render to strings; this is used for logging.

Methods
-------

``stop()``:     Stop the event from being passed to any more handlers


.. _events_service:

Service events
==============

When the service starts running:

``cletus.events.PreStart``:     The service is about to start (``service``)
``cletus.events.PostStart``:    The service has started (``service``) and is
                                about to enter its main listen loop

When the service stops:

``cletus.events.PreStop``:  The service is about to stop
``cletus.events.PostStop``: The service has stopped, and main program execution
                            is about to resume after ``service.run()``

When the service restarts:
``cletus.events.PreRestart``:   The service is about to restart (``service``).
``cletus.events.PostRestart``:  The service has restarted (``service``)

For more information about events when restarting, see
:ref:`method_service_restart`.


Server events
=============

``cletus.events.ListenStart``
-----------------------------

The server is listening

Called between the ``service`` events ``PreStart`` and ``PostStart``, once
the server has opened its socket and started listening.

``cletus.events.ListenStop``
----------------------------

The server is no longer listening


Client events
=============

``cletus.events.Connect``
-------------------------

Client has connected (``client``)

Attributes:
:   ``client``:     Instance of :ref:`class_client`


.. _class_events_receive:

``cletus.events.Receive``
-------------------------
:   Client has sent data (``client``)
    
    Attributes:
    :   ``client``:     Instance of :ref:`class_client`
        ``data``:       Input data (a line, or 

``cletus.events.Disconnect``
:   Client has disconnected (``client``)

    Attributes:
    :   ``client``:     Instance of :ref:`class_client`


Shutdown events
---------------
``cletus.events.PreStop``:      ``service``: The service is about to stop
``cletus.events.Drop``:         ``server``: The server is no longer listening
``cletus.events.PostStop``:     ``service``: The service has stopped


.. _class_receiveevent:

``cletus.events.ReceiveEvent``
------------------------------

Triggered when the client receives data

Attributes:
:   ``client``:     Instance of :ref:`class_client`
    ``data``:       Raw input data


.. _event_handlers:

Event Handlers
==============

An event handler is a function or generator which is registered with the
Service using :ref:`method_service_listen` for certain classes of events.
It is passed the instance of the event.

Multiple handlers can listen to a single event; they will be called in the
order they are defined. If a handler does not want later handlers to receive
the event, it can call ``event.stop()``.

The handler can be a function or a generator. A function can return at any
point; any return value is ignored.

If the handler is a generator, and the event has a ``client`` attribute, the
handler can ``yield`` to capture the next line of input from the client (or in
:ref:`raw socket mode <setting_socket_raw>` the next chunk of data). It can
continue to ``yield`` to capture further lines. For example::

    @service.listen(cletus.events.Connect)
    def connect(event):
        event.client.write_raw('Welcome. Please enter your name: ')
        username = yield
        event.client.username = username
        event.client.write('Welcome, %s' % username)
        service.write_all('%s has connected' % username, exclude=event.client)

This handler is from the ``chat.py`` example. Note the use of ``write_raw``
instead of ``write``; this stops Cletus from adding a newline when it's sent to
the client, so they will type their name on the same line.


Writing custom events
=====================

Create a subclass of :ref:`class_events_event` and ensure it sets a docstring
or ``__str__`` for logging.

Handlers are matched by comparing classes, so you can have two classes with the
same name (as long as they are in separate modules).
