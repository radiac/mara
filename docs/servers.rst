==============
Server classes
==============

Each server has a corresponding client, which is created automatically when a new
connection is made.


SocketServer
============

This is a low-level socket server which reads and writes bytes.

.. autoclass:: mara.servers.socket.SocketServer
	:members:
	:show-inheritance:

.. autoclass:: mara.servers.socket.SocketClient
	:members:
	:show-inheritance:


TextServer
==========

This wraps the ``SocketServer`` to read and write text ``str``.

.. autoclass:: mara.servers.socket.TextServer
	:members:
	:show-inheritance:

.. autoclass:: mara.servers.socket.TextClient
	:members:
	:show-inheritance:
