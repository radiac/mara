from mara.contrib.rooms import BaseRoom, Exits, Exit, FakeExit
from mara import events

from .core import service

class Room(BaseRoom):
    service=service

# Define a room in code
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

# Load other rooms using yaml instantiator
from mara.storage.yaml import instantiate
@service.listen(events.PreStart)
def instantiate_rooms(event):
    """
    Now the service has collected its settings, make the relative path
    absolute and instantiate the rooms defined in YAML
    """
    path = service.settings.abspath('mud/rooms.yaml')
    instantiate(service, path)
