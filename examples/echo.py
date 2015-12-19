from __future__ import unicode_literals

from mara import Service, events
service = Service()

@service.listen(events.Receive)
def receive(event):
    event.client.write(event.data)

if __name__ == '__main__': # pragma: no cover
    service.run(
        # Raw socket mode to disable telnet negotiation
        socket_raw=True,
    )
