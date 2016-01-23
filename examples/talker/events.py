from __future__ import unicode_literals

from mara import events
from mara.contrib.users import event_add_user, DisconnectHandler
from mara.contrib.users.password import ConnectHandler

from .core import service, User


# Make sure client events know about the user
service.listen(events.Client, event_add_user)


# Add a handler to process new connections
class TalkerConnectHandler(ConnectHandler):
    msg_welcome_initial = 'Welcome to the Mara example talker!'
service.listen(events.Connect, TalkerConnectHandler(User))

# Add handler to process user disconnections
service.listen(events.Disconnect, DisconnectHandler)
