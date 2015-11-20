#!/usr/bin/python
import cletus
from cletus import events
service = cletus.Service()

# Set up a filter for write_all to filter to users who have logged in,
# otherwise they'll see things on the login prompt
def filter_to_users(service, clients, **kwargs):
    return (c for c in clients if hasattr(c, 'username'))
service.filter_all = filter_to_users

@service.listen(events.Connect)
def connect(event):
    """Deal with connection"""
    event.client.write_raw('Welcome. What is your name? ')
    username = yield
    event.client.username = username
    event.client.write('Welcome, %s' % username)
    service.write_all('-- %s has connected --' % username, exclude=event.client)


@service.listen(events.Disconnect)
def disconnect(event):
    """Deal with disconnection"""
    # If the client doesn't have a username, it hasn't connected
    if not hasattr(event.client, 'username'):
        return
    service.write_all('-- %s has disconnected --' % event.client.username)


# This example uses a simple custom command parser
# Define some constants for the commands
COMMAND_SAY     = ''
COMMAND_EMOTE   = 'me'
COMMAND_WHO     = 'who'
COMMAND_QUIT    = 'quit'

@service.listen(events.Receive)
def receive(event):
    """Deal with data from client"""
    # If the client doesn't have a username, it hasn't connected
    if not hasattr(event.client, 'username'):
        return

    # Parse input
    cmd = COMMAND_SAY
    data = event.data
    if data.startswith('/'):
        if ' ' in data:
            cmd, data = data[1:].split(' ', 1)
        else:
            cmd, data = data[1:], ''
        cmd = cmd.lower()
    
    # Handle commands
    if cmd == COMMAND_SAY:
        service.write_all('%s> %s' % (event.client.username, data))
    elif cmd == COMMAND_EMOTE:
        service.write_all('%s %s' % (event.client.username, data))
    elif cmd == COMMAND_WHO:
        clients = ['  %s' % n for n in sorted(c.username for c in service.clients)]
        event.client.write('Users here at the moment:', *clients)
    elif cmd == COMMAND_QUIT:
        event.client.write('Goodbye!')
        event.client.close()
    else:
        event.client.write('Unknown command "%s"' % cmd)


if __name__ == '__main__':
    service.run(
        host='0.0.0.0',
        post=9000,
    )
