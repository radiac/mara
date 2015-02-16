===============
Getting started
===============

First, install cletus with

    pip install cletus

See :doc:`installation` for more details.


A Minimal Service
=================

A minimal Cletus service looks something like this::

    from cletus import Service
    service = Service()
    
    @service.listen(cletus.events.Receive)
    def receive(event):
        event.client.write(event.data)

    if __name__ == '__main__':
        service.run()

Save it as ``echo.py`` and run it:

    python echo.py
    * Running on 127.0.0.1:9000

Now connect to telnet://127.0.0.1:9000 and anything you enter will be sent back
to you - you have built a simple echo server.

Lets look at the code in more detail:

1. First we import :ref:`class_service` and create an instance of it.

   This ``service`` will be at the core of everything we do with Cletus; it
   manages settings, the server, keeps track of clients, and handles events.

2. Next we listen to one of those events using the :ref:`method_service_listen`
   decorator on a function definition.

3. When an event of the type :ref:`class_receiveevent` is triggered, this
   function will be called with the event object as the only argument.
   
   The event object contains all the relevant information about that event - in
   this case the ``event.client`` and ``event.data``.

4. The ``client`` attribute is an instance of :ref:`class_client`, which
   provides the ``write()`` method to send data. We just send back the raw data
   we received.

5. Lastly we call the :ref:`method_service_run` method on the service to
   collect any settings from the command line and start the server.

Client event handlers can also prompt the client for input by using ``yield`` -
see :ref:`event_handlers` for more details.

Event handlers (or sub-handlers, like ``command``) are the primary way you'll
interact with your service.


More examples
-------------

This echo server is in the ``examples`` directory of the Cletus source, along
with several more examples which will help get a feel for what Cletus can do,
and how you can develop with it:

echo.py:        The echo server shown above
chat.py:        A simple IRC-like chat server
run_talker.py:  A talker with support for commands and rooms


.. _settings:

Overriding settings
===================

Settings are collected in the following order, with last-defined being the
setting that wins:

1. Default settings in :ref:`module_settings`
2. Settings sources passed to ``service.run`` as non-keyword arguments
   * In addition to normal settings sources in strings, you can also provide a
     reference to an imported python module
3. Settings passed to ``service.run`` as keyword arguments
4. Settings sources passed as non-keyword arguments on the command line
5. Settings in keyword arguments on command line options
   * To set a string or integer value, use ``--value=X``
   * To set a boolean True value, use ``--setting``
   * To set a boolean False value, use ``--no-setting``

Settings sources can be:
:   ``module:python.module``:   Name of python module to import
    ``/path/to/conf.json``:     Path to JSON file

If a setting source isn't found, an error will be raised.

Once loaded, settings will be available in a :ref:`class_settings` instance
on ``service.settings``.

Example of coded settings passed to ``service.run``, to override default
settings::

    from mymud import settings
    service.run(settings, 'settings.json', host='0.0.0.0', port='7000')

This will use the default settings, then the ``mymud.settings`` module, then
values in ``settings.json``, then set the host and port as specified.

Command line example to override default and coded settings::

    python run_mymud.py module:mymud.dev dev.json --host=10.0.0.11 --port=8000

This will use the default settings and coded settings, then load them from
``mymud.dev`` module, then ``dev.json``, then set the host and port as
specified.


.. _logging:

Logging
=======

Rather than using python's standard logging, Cletus provides its own logger
for each service instance, with more customisability for what you want to log.

The default logging levels are:

* ``all``: select all logging levels
* ``service``: when the process starts or stops
* ``server``: when the server listens to a socket or disconnects
* ``client``: when a client connects or disconnect
* ``event``: when events are triggered
* ``debug``: all other events

Your logging level will be controlled by the setting ``log_level``

Your code can log to the default levels by calling the logging methods on
``service.log`` (``service(*lines)`` etc), or it can specify its own logging
levels by passing a different level string to :ref:`method_logger_write`.

