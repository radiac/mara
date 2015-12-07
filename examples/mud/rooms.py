from mara.contrib.rooms import BaseRoom, Exits, Exit, FakeExit
from mara import events

from .core import service

class Room(BaseRoom):
    service=service


room_lobby = Room(
    'lobby',
    name='Lobby',
    short='in the lobby',
    desc="You are in a room with a tall ceiling and a reception desk.",
    exits=Exits(
        north=Exit('pool'),
        south=FakeExit(
            'outside',
            "You think about leaving, but decide it's nice here.",
        ),
        east=Exit('clone_zone'),
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

clone_zone = Room(
    'clone_zone',
    name='Clone zone',
    clone=True,
    intro=(
        "Everything shimmers as reality seems to distort for a moment."
    ),
    short='in the clone zone',
    desc=(
        "In the clone zone, no-one can hear you scream. Or, in fact, do "
        "anything at all. You are forever alone."
    ),
    exits=Exits(
        west=Exit('lobby'),
    ),
)
