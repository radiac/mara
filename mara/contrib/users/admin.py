"""
Admin mixin for BaseUser, to allow users to be marked as admins

To set first admin, either register cmd_set_admin without an availability
restriction, or set it manually:
* connect and create account
* disconnect
* manually edit store/user/username.json
* change:
    "is_admin": false 
  to:
    "is_admin": true
"""
from __future__ import unicode_literals

from ..commands import define_command, RE_WORD
from ... import storage
from ... import util
from ... import styles

__all__ = [
    'AdminMixin', 'if_admin',
    'cmd_list_admin', 'cmd_set_admin', 'register_cmds',
]


class AdminMixin(storage.Store):
    """
    Mark users as admins
    """
    abstract = True
    is_admin = storage.Field(default=False)


def if_admin(event):
    """
    Return True if the user is an admin.
    
    For use as a command availability callback.
    
    Example::
    
        @commands.register(can=if_admin)
        def cmd_special(event):
            ...
    
    """
    return event.user.is_admin is True


###############################################################################
############################################################### Commands
###############################################################################

@define_command(help='List admin users')
def cmd_list_admin(event):
    """
    List admin users
    """
    User = event.user.__class__
    
    # List active admins
    active = [
        user.name for user in sorted(User.manager.active().values())
        if user.is_admin
    ]
    if active:
        event.user.write(
            styles.hr('Admin users here now'),
            util.pretty_list(active)
        )
    
    # List saved admins
    saved = [
        user.name for user in sorted(User.manager.saved().values())
        if user.is_admin
    ]
    if saved:
        event.user.write(
            styles.hr('Admin users who are offline'),
            util.pretty_list(saved)
        )
    
    if saved or active:
        event.user.write(styles.hr)
    else:
        event.user.write('There are no admin users')


@define_command(
    args=r'^%s (on|off)$' % RE_WORD,
    syntax='<username> <on|off>',
    help='Set a user to admin'
)
def cmd_set_admin(event, username, state):
    """
    Set or unset a user as an admin
    
    Should probably be used with: can=if_admin
    """
    # Find user
    User = event.user.__class__
    user = User.manager.load(username, active=False)
    if user is None:
        event.user.write('That user is not found')
        return
    
    user.is_admin = (state.lower() == 'on')
    user.save()
    if user.is_admin:
        event.user.write('%s is an admin' % user.name)
    else:
        event.user.write('%s is not an admin' % user.name)


###############################################################################
############################################################# Command shortcut
###############################################################################

def register_cmds(registry):
    """
    Shortcut to register all admin commands with default names
    """
    registry.register('admin', cmd_list_admin)
    registry.register('set_admin', cmd_set_admin, can=if_admin)
