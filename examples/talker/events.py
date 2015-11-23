import re

from mara import events
from mara import util
from mara.contrib.users.password import ConnectHandler

from .core import service
from .users import User


@service.listen(events.Receive)
def command_alias(event):
    """
    De-alias command aliases
    """
    # This will be attached to Receive event before standard CommandHandler
    if event.data.startswith("'"):
        event.data = 'say ' + event.data[1:]
    elif event.data.startswith(';'):
        event.data = 'emote ' + event.data[1:]

# Add a handler class to process new connections
class TalkerConnectHandler(ConnectHandler):
    msg_welcome_initial = 'Welcome to the Mara example talker!'
service.listen(events.Connect, TalkerConnectHandler(User))


@service.listen(events.Disconnect)
def disconnect(event):
    """Deal with disconnection"""
    # If the client doesn't have a user, it hasn't logged in
    if not getattr(event.client, 'user', None):
        return
    
    # Disconnect the user
    event.user.disconnected()
    service.write_all('-- %s has disconnected --' % event.user.name)
