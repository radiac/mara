"""
Room-related commands
"""
from __future__ import unicode_literals

from ..users import commands as user_cmds

from . import constants
from .. import commands
from ... import events

__all__ = [
    # Standard commands referenced/overridden from contrib.users
    'cmd_say', 'cmd_emote', 'cmd_tell',
    'cmd_look', 'cmd_list_active_users', 'cmd_list_all_users',
    
    # Room-specific commands
    'cmd_exits', 'cmd_where',
    
    # Navigation command generator
    'gen_nav_cmds',
    
    # Shortcut
    'register_cmds', 'register_aliases',
]


###############################################################################
################################################################ Standard cmds
###############################################################################

class RoomHandler(events.Handler):
    def get_container(self, event):
        return event.user.room

# Override container
class cmd_say(RoomHandler, user_cmds.cmd_say): pass
class cmd_emote(RoomHandler, user_cmds.cmd_emote): pass

# Nothing to override; add reference to this module for others to import
cmd_tell = user_cmds.cmd_tell
cmd_list_active_users = user_cmds.cmd_list_active_users
cmd_list_all_users = user_cmds.cmd_list_all_users

# Override container and functionality
class cmd_look(RoomHandler, user_cmds.cmd_look):
        # Change what the user sees
    def handler_10_user(self, event):
        event.user.room.look(event.user)


###############################################################################
################################################################ Room-specific
###############################################################################

@commands.define_command()
def cmd_exits(event):
    "List available exits"
    event.user.write(event.user.room.exits.get_desc())


@commands.define_command(args=r'^(\w+)?$', syntax='[<user>]')
def cmd_where(event, username=None):
    "See the location of yourself or another user"
    if not username:
        event.user.write('You are %s' % event.user.room.get_short())
        return
    
    user = event.user.manager.get_active_by_name(username)
    event.user.write('%s is %s' % (user.name, user.room.get_short()))


@commands.define_command(args=r'^(\w+)$', syntax='<room_id>')
def cmd_goto(event, room_key):
    "Go to a room, specified by internal id"
    Room = event.user.room
    room = Room.manager.get(room_key)
    if not room:
        event.user.write('Room "%s" not found.' % room_key)
        return
    
    # Jump to the new room
    room.enter(event.user)


@commands.define_command(args=r'^(\w+)$', syntax='<user>')
class cmd_bring(events.Handler):
    "Bring a user to your room"
    source_msg = 'You bring %(target)s to you'
    target_msg = '%(source)s brings you to them'
    
    def handler_10_find(self, event, username):
        self.target = event.user.manager.get_active_by_name(username)
    
    def handler_20_notify(self, event, username):
        event.user.write(self.source_msg % {'target': self.target.name})
        self.target.write(self.target_msg % {'source': event.user.name})
    
    def handler_30_move(self, event, username):
        event.user.room.enter(self.target)


###############################################################################
################################################################ Navigation
###############################################################################

def gen_nav_cmd(registry, verb, direction):
    """
    Build and register a navigational command to move a user between rooms
    
    Events must have a ``user`` attribute (see contrib.users.event_add_user),
    which must have the contrib.rooms.room.RoomUserMixin (or provide a similar
    interface).
    """
    def command(event):
        event.user.move(direction)
    registry.register(verb, command, group='nav')

def gen_nav_cmds(registry):
    """
    Build and register navigation commands for users to move between rooms
    """
    # Build directions
    for direction in constants.DIRECTIONS:
        gen_nav_cmd(registry, direction, direction)

    # Add aliases
    for alias, direction in constants.SHORT_DIRECTIONS.items():
        gen_nav_cmd(registry, alias, direction)


###############################################################################
################################################################ Shortcut
###############################################################################

def register_cmds(registry, admin=False):
    """
    Shortcut to register all standard room commands with default names
    
    Includes room-aware versions of the ones in contrib.users.register_cmds
    
    If using contrib.users.admin, set the optional argument ``admin=True``;
    this will limit the use of sensitive commands to admin users.
    """
    if_admin = None
    if admin:
        from ..users.admin import if_admin
    
    # Standard commands referenced/overridden from contrib.users
    registry.register('say', cmd_say)
    registry.register('emote', cmd_emote)
    registry.register('tell', cmd_tell)
    registry.register('look', cmd_look)
    registry.register('who', cmd_list_active_users)
    registry.register('users', cmd_list_all_users)

    # Room-specific commands
    registry.register('exits', cmd_exits)
    registry.register('where', cmd_where)
    
    # Admin commands
    registry.register('goto', cmd_goto, can=if_admin)
    registry.register('bring', cmd_bring, can=if_admin)
    
    # Nav commands
    gen_nav_cmds(registry)

def register_aliases(registry):
    """
    Shortcut to register common aliases
    
    Includes the ones defined by contrib.users.register_aliases
    """
    # Use the standard ones in contrib.users
    user_cmds.register_aliases(registry)
    
    # Add navigation aliases
    for alias, cmd in constants.SHORT_DIRECTIONS.items():
        registry.alias(r'^%s$' % alias, cmd)
