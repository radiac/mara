import cletus
service = cletus.Service()

@service.listen(cletus.events.Receive)
def receive(event):
    event.client.write(event.data)

if __name__ == '__main__':
    service.run()
