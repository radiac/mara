=========
Upgrading
=========

For an overview of what has changed between versions, see the :ref:`changelog`.


Instructions
============

1. Check which version of Mara you are upgrading from::

    python
    >>> import mara
    >>> mara.__version__

2. Upgrade the Mara package::

    pip install --upgrade mara

3. Find your version below and work your way up this document until you've upgraded to
   the latest version


.. _upgrade_0-6-3:

Upgrading from 0.6.3
====================

Mara 0.6.3 was the last release of version 1 of Mara. Although Version 2 has a similar
API, it is a complete rewrite and most user code will need to be updated and refactored.

The key differences are:

* ``mara.Service`` is now ``mara.App``, and now uses asyncio.
* Servers must be defined and added using ``add_server``
* Event handlers need to be ``async``. Handler classes have been removed. To capture
  user data a handler must ``await event.client.read()`` instead of calling ``yield``.
* Timers are now defined as instances.
* All contrib modules have been removed in version 2. These will be brought back as a
  separate package.
* Version 2.0.0 is missing the angel, ``mara`` command, and telnet support.
  These are planned for a future version.
