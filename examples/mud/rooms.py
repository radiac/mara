from mara.contrib.rooms import BaseRoom, Exits, Exit, FakeExit
from mara import events

from .core import service

class Room(BaseRoom):
    service=service


room_lobby = Room(
    'lobby',
    name='Lobby',
    short='in the lobby',
    desc="You are standing in a room with a tall ceiling and a reception desk",
    exits=Exits(
        north=Exit('pool'),
        south=FakeExit(
            'outside',
            "You think about leaving, but decide it's nice here.",
        ),
    ),
)

room_pool = Room(
    'pool',
    name='Pool',
    short='by the pool',
    desc="A narrow path follows the edge of the pool around the room.",
    exits=Exits(
        south=Exit('lobby'),
    ),
)

