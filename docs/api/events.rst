======
Events
======


.. _event_handlers:

Event Handlers
==============

An event handler is a function, generator or :ref:`class_events_handler`, which
is registered with the service using :ref:`method_service_listen` for certain
classes of events. It is passed the instance of the event, and handlers are
able to modify it for future handlers if they wish.

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
        event.client.write('Welcome. Please enter your name: ', newline=False)
        username = yield
        event.client.username = username
        event.client.write('Welcome, %s' % username)
        service.write_all('%s has connected' % username, exclude=event.client)

This handler is from the ``chat.py`` example. Note that the first call to
``write`` sets ``newline=False``; this stops Mara from adding a newline to the
end of the line when it's sent to the client, so they will type their name on
the same line.


.. _class_events_handler:

``mara.events.Handler``
-----------------------

Event handler base class.

Event handlers can be stand-alone functions or generators, but you can also
use the ``Handler`` class to create compound handlers which can be designed
to be inherited from and overridden.

Any methods on the class with a name starting ``handler_`` will be run in
alphanumeric name order - so if order is important to you, use a number in your
method name to ensure clear ordering, eg ``handler_10_get_name``.

Each handler method can be a functions or a generator. Because calling a
sub-generator in python 2.7 is a pain, this makes the ``Handler`` class the
easiest way to write re-usable event handlers which rely on user input.

Each handler method is passed two arguments:
    self
        Reference to the handler class
    event
        The event which triggered this handler class. This is also available
        on self.event.

There are two ways to manage flow between handler methods:

* Calls to ``event.stop()`` are respected; no further handler methods will be
  called once an event is stopped
* Modify ``self.handlers`` - this is the queue of remaining handlers to run.
  It is a simple list of method references; add or remove items as needed. You
  can reset it to the full list of handlers by using ``get_handlers()``::

        def handler_infinite_loop(self):
            "This is very silly and will lock up your service"
            self.handlers = self.get_handlers()

For an example of a more complex event handler, see the ``ConnectHandler``
classes in :ref:`module_contrib_users` and
:ref:`module_contrib_users_password`.

Event handlers are compatible with the :ref:`module_contrib_commands` module;
see :ref:`contrib_commands_handlers` for more details.


.. _event_inheritance:

Event inheritance
=================

It is often desirable to bind a handler to listen to a category of events; for
example, when you want to extend all client events by adding a user attribute
to them, as is done with :ref:`module_contrib_users`.

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

This means that the order that handlers are bound is still respected.


Writing custom events
=====================

Create a subclass of :ref:`class_events_event` and ensure it sets a docstring
or ``__str__`` for logging.

Handlers are matched by comparing classes, so you can have two classes with the
same name (as long as they are in separate modules).


Event classes
=============

.. _class_events_event:

``mara.events.Event``
---------------------

Base class for event classes.

Events are containers for event data; event attributes are passed as keyword
arguments to the constructor. For example::

    event = mara.events.Receive(client=client_obj, data=raw_data)

Events can render to strings; this is used for logging.

Methods:

``stop()``
~~~~~~~~~~
Stop the event from being passed to any more handlers


.. _events_service:

Service events
--------------

These are subclasses of the ``mara.events.Service`` event.

When the service starts running:

    ``mara.events.PreStart``
        The service is about to start its server (``service.server`` is not
        yet defined). Settings have been collected, a connection to the angel
        (if present) has been established, and the logger has been initialised.
        
    ``mara.events.PostStart``
        The server has been initialised and is about to enter its main listen
        loop. If the process is restarting, the clients and stores have now
        been deserialised.

When the service stops:

    ``mara.events.PreStop``
        The service is about to stop its server by telling it to terminate its
        main listen loop. This is the last opportunity to write to clients -
        but flush them to make sure the data gets to them.
        
    ``mara.events.PostStop``
        The server has left its main listen loop and has closed its socket and
        those of its clients. Main program execution is about to resume from
        where it called ``service.run()``

When the service restarts:
    
    ``mara.events.PreRestart``
        The service is about to restart the process. It has confirmed that it
        is connected to the angel and can proceed; it is about to flush client
        sockets, suspend the server, serialise all client sockets and store
        data and send it to the angel, before terminating this process.
    
    ``mara.events.PostRestart``
        The service has restarted. This is called immediately after
        ``PostStart``, so everything has been deserialised now. This is a new
        process to the one which triggered the ``PreRestart``.

For more information about events when restarting, see
:ref:`method_service_restart`.


Server events
-------------

These are subclasses of the ``mara.events.Server`` event.

``mara.events.ListenStart``
~~~~~~~~~~~~~~~~~~~~~~~~~~~
The server is listening.

Called between the ``service`` events ``PreStart`` and ``PostStart``, once
the server has opened its socket and started listening.

``mara.events.ListenStop``
~~~~~~~~~~~~~~~~~~~~~~~~~~
The server is no longer listening


Client events
-------------

These are subclasses of the ``mara.events.Client`` event.

``mara.events.Connect``
~~~~~~~~~~~~~~~~~~~~~~~

Client has connected (``client``)

Attributes:
    ``client``
        Instance of :ref:`class_client`


.. _class_events_receive:

``mara.events.Receive``
~~~~~~~~~~~~~~~~~~~~~~~

Client has sent data (``client``).

When in raw mode this will be triggered as soon as data arrives on the socket,
but when raw mode is disabled (by default), incoming data will be buffered
until one or more newline sequences are found; at that point a new event will
be created for each complete line.
    
Attributes:
    ``client``
        Instance of :ref:`class_client`

    ``data``
        Input data. When in raw mode this will be the unmodified data exactly
        as it arrives, but when raw mode is disabled (by default), this is a
        single full line of input, with newline stripped and any telnet
        negotiation sequences removed.


``mara.events.Disconnect``
~~~~~~~~~~~~~~~~~~~~~~~~~~

Client has disconnected (``client``)

Attributes:
    ``client``
        Instance of :ref:`class_client`

