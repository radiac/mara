"""
Room-related commands
"""
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
    'register_cmds',
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



@commands.define_command(args=r'(\w+)?', syntax='[<user>]')
def cmd_where(event, username=None):
    if not username:
        event.user.write('You are %s' % event.user.room.get_short())
        return
    
    user = event.user.manager.get_active_by_name(username)
    event.user.write('%s is %s' % (user.name, user.room.get_short()))


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

def register_cmds(registry):
    """
    Shortcut to register all standard room commands with default names
    """
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
    gen_nav_cmds(registry)
