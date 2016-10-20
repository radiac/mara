=======================================
Mara - Python network service framework
=======================================

An event-based python framework designed for building TCP/IP services, such as
echo servers, flash policy servers, chatrooms, talkers and MUDs. Batteries
included.

* Project site: http://radiac.net/projects/mara/
* Source code: https://github.com/radiac/mara

.. image:: https://travis-ci.org/radiac/mara.svg?branch=master
    :target: https://travis-ci.org/radiac/mara

.. image:: https://coveralls.io/repos/radiac/mara/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/radiac/mara?branch=master


Features
========

* Event-based framework with support for timers
* Supports raw sockets or telnet with negotiation
* Supports seamless restarts while maintaining connections and state
* Common extras included, such as:

  * command manager
  * storage system
  * natural language processing tools
  * accounts, login helpers and rooms

Version 0.6.1. Supports Python 2.7 and 3.2 to 3.5.

See the `Documentation <http://radiac.net/projects/mara/documentation/>`_
for details of how Mara works.


Quickstart
==========

Install Mara with ``pip install mara``, then write your service using
`event handlers <http://radiac.net/projects/mara/documentation/api/events/>`_.

A minimal Mara service looks something like this::

    from mara import Service
    service = Service()

    @service.listen(mara.events.Receive)
    def receive(event):
        event.client.write(event.data)

    if __name__ == '__main__':
        service.run()

Save it as ``echo.py`` and run it::

    python echo.py
    * Server listening on 127.0.0.1:9000

Override settings `in code <http://radiac.net/projects/mara/documentation/introduction/#settings>`_,
or by passing arguments on the command line::

    python echo.py --host=10.0.0.11 --port=8000
    * Server listening on 10.0.0.11:8000

Take a look at the
`examples <https://github.com/radiac/mara/tree/master/examples>`_ to see how to
start writing more complex services, or read the
`documentation <http://radiac.net/projects/mara/documentation/>`_ for
details of how Mara works.
