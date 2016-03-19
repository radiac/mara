from __future__ import unicode_literals

from mara import events
from mara.contrib.rooms import (
    room_restart_handler_factory, RoomConnectHandler, event_add_room_container,
)
from mara.contrib.users import event_add_user, DisconnectHandler
from mara.contrib.users.password import ConnectHandler

from .core import service
from .users import User
from .rooms import room_lobby


# Make sure client events know about the user and the room
# These must be the first two events, in this order
service.listen(events.Client, event_add_user)
service.listen(events.Client, event_add_room_container)


# Add handler to process new connections
class MudConnectHandler(RoomConnectHandler, ConnectHandler):
    msg_welcome_initial = 'Welcome to the Mara example mud!'
    default_room = room_lobby
service.listen(events.Connect, MudConnectHandler(User))

# Add handler to process user disconnections
service.listen(events.Disconnect, DisconnectHandler)

# Add restart handler to reconnect users to their rooms
service.listen(
    events.PostRestart, room_restart_handler_factory(User, room_lobby)
)
