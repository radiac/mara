======
Events
======

.. _class_events_event:

``mara.events.Event``
=====================

Base class for event classes.

Events are containers for event data; event attributes are passed as keyword
arguments to the constructor. For example::

    event = mara.events.Receive(client=client_obj, data=raw_input)

Events can render to strings; this is used for logging.


Methods
-------

``stop()``:     Stop the event from being passed to any more handlers


.. _events_service:

Service events
==============

These are subclasses of the ``mara.events.Service`` event.

When the service starts running:

``mara.events.PreStart``:     The service is about to start (``service``)
``mara.events.PostStart``:    The service has started (``service``) and is
                                about to enter its main listen loop

When the service stops:

``mara.events.PreStop``:  The service is about to stop
``mara.events.PostStop``: The service has stopped, and main program execution
                            is about to resume after ``service.run()``

When the service restarts:
``mara.events.PreRestart``:   The service is about to restart (``service``).
``mara.events.PostRestart``:  The service has restarted (``service``)

For more information about events when restarting, see
:ref:`method_service_restart`.


Server events
=============

These are subclasses of the ``mara.events.Server`` event.

``mara.events.ListenStart``:      The server is listening.
                                    Called between the ``service`` events
                                    ``PreStart`` and ``PostStart``, once
                                    the server has opened its socket and
                                    started listening.
``mara.events.ListenStop``:       The server is no longer listening


Client events
=============

These are subclasses of the ``mara.events.Client`` event.

``mara.events.Connect``
-------------------------

Client has connected (``client``)

Attributes:
:   ``client``:     Instance of :ref:`class_client`


.. _class_events_receive:

``mara.events.Receive``
-----------------------
:   Client has sent data (``client``)
    
    Attributes:
    :   ``client``:     Instance of :ref:`class_client`
        ``data``:       Input data (a line, or 

``mara.events.Disconnect``
:   Client has disconnected (``client``)

    Attributes:
    :   ``client``:     Instance of :ref:`class_client`



.. _event_handlers:

Event Handlers
==============

An event handler is a function or generator which is registered with the
Service using :ref:`method_service_listen` for certain classes of events.
It is passed the instance of the event.

Multiple handlers can listen to a single event; they will be called in the
order they are defined. If a handler does not want later handlers to receive
the event, it can call ``event.stop()``.

Events also are bubbled up to superclass handlers - see
:ref:`event_inheritance` for more details.

The handler can be a function or a generator. A function can return at any
point; any return value is ignored.

If the handler is a generator, and the event has a ``client`` attribute, the
handler can ``yield`` to capture the next line of input from the client (or in
:ref:`raw socket mode <setting_socket_raw>` the next chunk of data). It can
continue to ``yield`` to capture further lines. For example::

    @service.listen(mara.events.Connect)
    def connect(event):
        event.client.write_raw('Welcome. Please enter your name: ')
        username = yield
        event.client.username = username
        event.client.write('Welcome, %s' % username)
        service.write_all('%s has connected' % username, exclude=event.client)

This handler is from the ``chat.py`` example. Note the use of ``write_raw``
instead of ``write``; this stops Mara from adding a newline when it's sent to
the client, so they will type their name on the same line.


Event inheritance
-----------------

It is often desirable to bind a handler to listen to a category of events; for
example, when you want to extend all client events by adding a user attribute
to them, as is done with :ref:`class_contrib_users`.

To make this easy, Mara lets you bind a handler to an event base class. For
example, a handler bound to ``events.Client`` will also be called for
``Receive``, ``Connect`` and ``Disconnect`` events.

.. warning::
    If you have an event listener which triggers a subclass of that event, be
    careful to avoid infinite loops; for example, you could check the event
    class before triggering it, eg::
    
        class Subevent(mara.events.Receive): pass
        
        @service.listen(mara.events.Receive)
        def receiver(event):
            if type(event) == mara.events.Receive:
                # Safe to trigger subevent
                service.trigger(Subevent(...))
            else:
                # This could be the subevent

Behind the scenes manages this in two ways:
* when binding a handler, the service adds finds subclasses of the specified
  event and binds the handler to those too
* when a service sees a new event class (when binding or triggering) it looks
  at the bound handlers for its base class, and binds those to the new event
  class. If a class has multiple base classes, only the first one is used.


Writing custom events
=====================

Create a subclass of :ref:`class_events_event` and ensure it sets a docstring
or ``__str__`` for logging.

Handlers are matched by comparing classes, so you can have two classes with the
same name (as long as they are in separate modules).
