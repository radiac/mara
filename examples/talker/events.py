from mara import events

from .core import service, User


# Make sure client events know about the user
from mara.contrib.users import event_add_user
service.listen(events.Client, event_add_user)

# Add a handler to process new connections
from mara.contrib.users.password import ConnectHandler
class TalkerConnectHandler(ConnectHandler):
    msg_welcome_initial = 'Welcome to the Mara example talker!'
service.listen(events.Connect, TalkerConnectHandler(User))

# Add handler to process user disconnections
from mara.contrib.users import DisconnectHandler
service.listen(events.Disconnect, DisconnectHandler)
