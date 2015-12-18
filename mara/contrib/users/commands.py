"""
Common commands for user-based services

Commands which write to the container are handlers, so they can be directed
to write to container other than the service.

Commands which have a specific display style are also handlers, so the display
code can be overridden while still using the same logic for preparing data.
"""
from __future__ import unicode_literals

from ..commands import define_command, MATCH_STR, RE_LIST
from ... import events
from ... import util
from ... import styles

__all__ = [
    # Standard commands
    'cmd_say', 'cmd_emote', 'cmd_tell',
    'cmd_look', 'cmd_list_active_users', 'cmd_list_all_users',
    
    # Shortcut
    'register_cmds', 'register_aliases',
]


###############################################################################
################################################################ Standard cmds
###############################################################################

@define_command(args=MATCH_STR, syntax='<message>')
class cmd_say(events.Handler):
    """
    Say something to the other users
    """
    def handler_10_do(self, event, message):
        event.client.write("You say: %s" % message)
        self.container.write_all(
            "%s says: %s" % (event.user.name, message),
            exclude=event.client,
        )


@define_command(args=MATCH_STR, syntax='<action>')
class cmd_emote(events.Handler):
    """
    Emote something to the other users
    """
    def handler_10_do(self, event, action):
        if not action.startswith("'"):
            action = ' ' + action
        self.container.write_all("%s%s" % (event.user.name, action))


@define_command(
    args=r'^' + RE_LIST + '\s+(?P<msg>.*?)$',
    syntax='<user>[, <user>] <message>',
)
def cmd_tell(event, usernames, msg):
    """
    Tell one or more users something
    """
    usernames = [a.strip() for a in usernames.split(',')]
    users = event.user.manager.get_active_by_name(usernames)
    
    # Validate target user
    if event.user.name.lower() in users:
        event.client.write('Why would you want to tell yourself that?')
        return
        
    # Send
    user_objs = users.values()
    for target in user_objs:
        targets = util.pretty_list(['you'] + sorted(
            [user.name for user in user_objs if user != target]
        ))
        target.client.write(
            '%s tells %s: %s' % (event.user.name, targets, msg),
        )
    event.client.write('You tell %s: %s' % (
        util.pretty_list(sorted([u.name for u in user_objs])),
        msg,
    ))


@define_command()
class cmd_look(events.Handler):
    """
    Look around
    """
    def handler_10_container(self, event):
        self.container.write_all(
            '%s looks around' % event.user.name,
            exclude=event.client,
        )
    
    def handler_10_user(self, event):
        event.user.write(
            self.container.get_who(exclude=event.user.client),
        )


@define_command()
class cmd_list_active_users(events.Handler):
    def handler_10_collect(self, event):
        # Find users
        self.users = event.user.manager.active().values()
        self.users.sort(key=lambda user: user.name)
    
    def handler_20_display(self, event):
        # Build lines of output
        lines = [styles.hr('Currently online')]
        for user in self.users:
            lines.append(
                "%s\t%s" % (user.name, user.client.get_idle_age())
            )
        lines.append(styles.hr)
        
        # Write to the user
        event.client.write(*lines)


@define_command()
class cmd_list_all_users(events.Handler):
    """
    List all online and offline users
    """
    def handler_10_collect(self, event):
        manager = event.user.manager
        self.online = [user.name for user in sorted(manager.active().values())]
        self.offline = [user.name for user in sorted(manager.saved().values())]
    
    def handler_20_display(self, event):
        event.user.write(
            styles.hr('Users'),
            'Online: ' + util.pretty_list(self.online),
            'Offline: ' + util.pretty_list(self.offline),
            styles.hr,
        )


###############################################################################
################################################################ Shortcut
###############################################################################

def register_cmds(registry):
    """
    Shortcut to register all standard user commands with default names
    """
    registry.register('say', cmd_say)
    registry.register('emote', cmd_emote)
    registry.register('tell', cmd_tell)
    registry.register('look', cmd_look)
    registry.register('who', cmd_list_active_users)
    registry.register('users', cmd_list_all_users)

def register_aliases(registry):
    """
    Shortcut to register common aliases
    """
    registry.alias(r"^'", 'say ')
    registry.alias(r'^;', 'emote ')
    registry.alias(r'^>', 'tell ')
    registry.alias(r'^l$', 'look')
