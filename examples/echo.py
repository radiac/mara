from mara import Service, events
service = Service()

@service.listen(events.Receive)
def receive(event):
    event.client.write(event.data)

if __name__ == '__main__': # pragma: no cover
    service.run()
