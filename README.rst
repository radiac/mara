=======================================
Mara - Python network service framework
=======================================

An asynchronous event-based python framework designed for building TCP/IP services, such
as telnet, HTTP and websocket servers.

.. image:: https://img.shields.io/pypi/v/mara.svg
    :target: https://pypi.org/project/mara/
    :alt: PyPI

.. image:: https://github.com/radiac/mara/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/radiac/mara/actions/workflows/ci.yml
    :alt: Tests

.. image:: https://codecov.io/gh/radiac/mara/branch/main/graph/badge.svg?token=BCNM45T6GI
    :target: https://codecov.io/gh/radiac/mara
    :alt: Test coverage


* Project site: https://radiac.net/projects/mara/
* Source code: https://github.com/radiac/mara


Features
========

* Asynchronous event-based framework
* Supports multiple servers

Requires Python 3.10 or later, see installation.

See the `Documentation <http://radiac.net/projects/mara/documentation/>`_
for details of how Mara works.

Note: Version 2.0.z is in development, and the API is subject to change without notice.
The last release to support Python 2 and 3.9 was version 0.6.3.


Quickstart
==========

Install Mara with ``pip install mara``, then write your service using
`event handlers <http://radiac.net/projects/mara/documentation/api/events/>`_.

A minimal Mara service looks something like this::

    from mara import App, events
    from mara.servers.socket import SocketServer

    app = App()
    app.add_server(SocketServer(host="127.0.0.1", port=9000))

    @app.listen(events.Receive)
    async def echo(event: events.Receive):
        event.client.write(event.data)

    app.run()


Save it as ``echo.py`` and run it::

    $ python echo.py
    Server listening: Socket 127.0.0.1:9000


Take a look at the
`examples <https://github.com/radiac/mara/tree/master/examples>`_ to see how to
start writing more complex services, or read the
`documentation <http://radiac.net/projects/mara/documentation/>`_ for
details of how Mara works.
