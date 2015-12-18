"""
Standard commands
"""
from __future__ import unicode_literals

from .core import define_command
from ... import styles


###############################################################################
################################################################ Definitions
###############################################################################

@define_command(args=r'^(?P<group>\w+)?$', syntax="(groups|<group>)")
def cmd_commands(event, group=None):
    """
    List commands
    """
    groups = event.registry.groups
    if group:
        if (group == 'groups' or group not in groups):
            event.client.write('Valid groups are: %s' % ', '.join(
                [name or '(None)' for name in groups.keys()]
            ))
            return
    
    groupname = ''
    if group:
        groupname = group.title() + ' '
    
    event.client.write(
        styles.hr('%sCommands' % groupname),
        ' '.join(
            (cmd.name for cmd in groups[group] if cmd.is_available(event))
        ),
        styles.hr,
    )
    
@define_command(
    args=r'^(?P<cmd>\w+)?$', syntax="<command>",
    help="Show help for a command",
)
def cmd_help(event, cmd=None):
    """
    Show help for a command
    
    Pass context={'commands': 'name of cmd_commands command'} to make the
    syntax error message more helpful.
    Recommend that registration overrides syntax with a reference to the 
    commands command, eg '<command>, or type "commands" to see a list of commands'
    """
    # Helpful syntax error
    if cmd is None:
        msg = 'Syntax: %s %s' % (event.match, event.command.syntax)
        if event.context and 'cmd_commands' in event.context:
            msg += ', or type %s to see a list of commands' % (
                event.context['cmd_commands']
            )
        event.client.write(msg)
        return
    
    # Look up command
    command = event.registry.commands.get(cmd)
    if command is None or not command.is_available(event):
        event.client.write('Unknown command')
        return
    
    syntax = 'Syntax: %s %s' % (command.name, command.syntax or '')
    
    if not command.help:
        event.client.write(syntax)
        return
    
    event.client.write(
        styles.hr('Help: %s' % command.name),
        command.help,
        '', syntax,
        styles.hr()
    )


@define_command(help="Restart the server")
def cmd_restart(event):
    if not event.service.angel:
        event.user.write('Cannot restart, running without angel')
        return
    
    event.exception_fatal = True
    event.service.write_all('-- Restarting server --')
    event.service.restart()


@define_command(help="Disconnect")
def cmd_quit(event):
    event.client.write(styles.hr('Goodbye!'))
    event.client.close()


###############################################################################
################################################################ Shortcut
###############################################################################

def register_cmds(registry, admin=False):
    """
    Shortcut to register all standard commands with default names
    
    If using contrib.users.admin, set the optional argument ``admin=True``;
    this will limit the use of sensitive commands to admin users.
    """
    if_admin = None
    if admin:
        from ..users.admin import if_admin
    
    registry.register('commands', cmd_commands)
    registry.register('help', cmd_help, context={'cmd_commands': 'commands'})
    registry.register('restart', cmd_restart, can=if_admin)
    registry.register('quit', cmd_quit)
