======================
Cletus the Chat Server
======================

A framework for building telnet-based services such as IRC-like chatrooms,
talkers or muds.

* Project site: http://radiac.net/projects/cletus/
* Source code: https://github.com/radiac/cletus

See the `Documentation <http://radiac.net/projects/cletus/documentation/>`_
for details of how Cletus works.


Features
========

* Event-based framework
* Supports raw sockets or telnet with negotiation
* Common extras included, such as a command manager and storage system


Quickstart
==========

Install Cletus with ``pip install cletus``, then write your service using
event handlers.

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
    * Server listening on 127.0.0.1:9000
