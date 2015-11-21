=========================================================
Mara - A framework for network services, talkers and MUDs
=========================================================

An event-based python framework designed for building TCP/IP services, such as
echo servers, flash policy servers, chatrooms, talkers and MUDs. Batteries
included.

* Project site: http://radiac.net/projects/mara/
* Source code: https://github.com/radiac/mara

See the `Documentation <http://radiac.net/projects/mara/documentation/>`_
for details of how Mara works.


Features
========

* Event-based framework with support for timers
* Supports raw sockets or telnet with negotiation
* Supports seamless restarts while maintaining connections
* Common extras included, such as:
  * command manager
  * storage system
  * accounts and login helpers
  * natural language processing tools


Quickstart
==========

Install Mara with ``pip install mara``, then write your service using
event handlers.

A minimal Mara service looks something like this::

    from mara import Service
    service = Service()
    
    @service.listen(mara.events.Receive)
    def receive(event):
        event.client.write(event.data)

    if __name__ == '__main__':
        service.run()

Save it as ``echo.py`` and run it:

    python echo.py
    * Server listening on 127.0.0.1:9000

Take a look at the
`examples <https://github.com/radiac/mara/tree/master/examples>`_ to see how to
start writing more complex services, or read the
`documentation <http://radiac.net/projects/mara/documentation/>`_ for
details of how Mara works.
