============
Contributing
============

Contributions are welcome, preferably via pull request. Check the github issues
and project :ref:`roadmap <roadmap>` to see what needs work, but Mara aims to
include as much common generic functionality as is practical - so if you write
something for your service which you think would be a good addition to contrib,
please do send it in.


Installing
==========

The easiest way to work on Mara is to fork the project on github, then install
it to a virtualenv::

    virtualenv mara
    cd mara
    source bin/activate
    pip install -e git://github.com/USERNAME/mara.git#egg=mara[full,dev]

(replacing ``USERNAME`` with your username).

This will also install all the dependencies you need for development and
testing; you'll find the Mara source ready for you to work on in the ``src``
folder of your virtualenv.


Testing
=======

It is greatly appreciated when contributions come with unit tests.

To run the tests with debug data::

    cd src/mara
    nosetests -s -vv

To run the tests without debug data::

    python setup.py test

To run the tests and generate a coverage report::

    tox

The Mara tests are in the ``tests`` folder; there are tests for each of the
example services, as well as any fragile areas of the code which make more
sense tested away from a server/client arrangement.


Code overview
=============

Mara is based around services, so start in ``mara.service``. The ``Service``
class is responsible for:

* collecting settings (work actually done by ``mara.settings.collector``)
* starting the server (in ``mara.connection.server``)
* handling events (event classes are in ``mara.events``)
* timers (managed by the ``Registry`` class in ``mara.timers.registry``)
* keeping track of its stores (a dict of ``Store`` subclasses, inheriting from
  ``mara.storage``)
* starting a restart (in ``Service.restart``), serialising and deserialising
  the server and stores (in ``Service.serialise`` and ``Service.deserialise``)
  and restoring the state after a restart (in ``Service.run``).

Mara does not use threads. When you call ``service.run()``, the service tells
the ``service.server`` to enter its main listen loop. This will run continually
until ``service.stop()`` is called as the result of an event (eg the
``restart`` command). The server loops continually, checking all connected
sockets for data to read; it uses ``select`` to time this operation out after
100ms (by default), at which point it calls ``service.poll()``, which in turn
runs any due/overdue timers.

If ``select`` finds that there is a socket with data to read, it will pass it
to a ``Client`` instance (from ``mara.connection.client``). In raw socket mode
this will immediately trigger a ``Receive`` event; otherwise the client
maintains an input buffer, parses the input for telnet negotiation commands,
and when it has received a full line it will trigger a ``Receive`` event.

The angel server (``Angel``) and client (``Process``) are defined in
``mara.angel``. When in angel mode, logging is passed up to the angel. The
angel script in ``bin/mara`` simply instantiates and runs the ``Angel`` class;
the ``Process`` class is instantiated and used in ``Service.run()``.

Lastly, anything which isn't classed as a core feature is defined in
``mara.contrib``. See the :doc:`api/contrib` docs for more information.


.. _roadmap:

Roadmap
=======

Planned but not scheduled for a specific version:
* More contrib modules:
  * Items and inventory
  * Combat (health, weapons and armour)
  * Improved natural language processing tools
  * NPCs
* SSH support
* Support for poll, epoll
