========
Cookbook
========

Tips and tricks for working with Mara


Capture user input
==================

Each client instance reads from its connection in its own async read loop, and raises a
``Receive`` event when data is received. This event is then handled within that client's
read loop, blocking any data from that client until the event is completely handled.

This means that an event can effectively pause the read loop for that client and capture
inbound content ``client.read()``::

    @app.listen(events.Connect)
    async def login(event: events.Connect):
        event.client.write("Username: ", end="")
        username: str = event.client.read()
        event.client.write(f"Welcome, {username}")

Here the ``client.read()`` will capture the first input from a user, and will not
trigger a ``Receive`` event.

Note that clients can write during an event, as outgoing data is sent using a separate
async write loop. You may want to call ``await event.client.flush()`` to ensure the data
has been sent before continuing.
