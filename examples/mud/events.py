from __future__ import unicode_literals

from mara import events

from .core import service
from .users import User
from .rooms import room_lobby


# Make sure client events know about the user
from mara.contrib.users import event_add_user
service.listen(events.Client, event_add_user)

# Add handler to process new connections
from mara.contrib.users.password import ConnectHandler
from mara.contrib.rooms import RoomConnectHandler
class MudConnectHandler(RoomConnectHandler, ConnectHandler):
    msg_welcome_initial = 'Welcome to the Mara example mud!'
    default_room = room_lobby
service.listen(events.Connect, MudConnectHandler(User))

# Add handler to process user disconnections
from mara.contrib.users import DisconnectHandler
service.listen(events.Disconnect, DisconnectHandler)

# Add restart handler to reconnect users to their rooms
from mara.contrib.rooms import room_restart_handler_factory
service.listen(
    events.PostRestart, room_restart_handler_factory(User, room_lobby)
)
