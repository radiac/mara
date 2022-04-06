===============
Getting started
===============

First, install mara with::

    pip install mara

See :doc:`installation` for more options and details.


A minimal service
=================

A minimal Mara service looks something like this::

    from mara import App, events
    from mara.servers.socket import SocketServer

    app = App()
    app.add_server(SocketServer(host="127.0.0.1", port=9000))

    @app.listen(events.Receive)
    async def echo(event: events.Receive):
        event.client.write(event.data)

    app.run()

Save this as ``echo.py`` and run it using ``python``::

    $ python echo.py
    Server listening: Socket 127.0.0.1:9000

Now connect to ``telnet://127.0.0.1:9000`` and anything you enter will be sent back to
you - you have built a simple echo server.


Lets look at the code in more detail:

#.  First we import ``App`` and create an instance of it.

    This ``app`` will be at the core of everything we do with Mara; it
    manages settings, servers, and handles events.

#.  Next we define and add our ``SocketServer``.

    There are different types of server, but this one is the simplest - it deals with
    raw bytes. If we wanted to run additional servers on other ports, we would define
    and add them here.

#.  Next we add an event handler, ``echo(...)``.

    We define an async function which accepts a single argument, ``event``, and then
    use the ``@app.listen`` decorator to register it with the app.

#.  When an event of the type ``Receive`` is triggered, the ``echo`` function will be
    called with the current event object as the only argument.

    The event object contains all the relevant information about that event - in
    this case the ``event.client`` and ``event.data``.

#.  We write the received data back to the client with ``event.client.write(...)``.

    The ``event.client`` attribute is an instance of ``SocketClient`` - our end of a
    specific connection. This provides the ``write()`` method to send data, and we just
    send back the raw data we received.

#.  Lastly we call the ``app.run()`` method.

    This starts the app's asyncio loop and runs the registered servers.
