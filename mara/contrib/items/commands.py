"""
Item-related commands
"""
from __future__ import unicode_literals

from .container import ItemContainerMixin
from .. import commands
from ... import events
from ... import utils


###############################################################################
# Standard cmds
###############################################################################


# ++ Really? This is dumb
# There must be a better way to extend commands. Extend the command registry
# or Handler base object to make it easy to override and extend a command
# which has already been registered (ie inject the mixin into bases)

class LookMixin(events.Handler):
    """
    Add this mixin to the cmd_look handler
    """
    # Display items in this container
    def handler_50_items(self, event):
        if not isinstance(self.container, ItemContainerMixin):
            continue
        event.client.write(*utils.pretty_list(
            self.container.get_items_display(depth=1, prose=True)
        ))


@commands.define_command()
def cmd_inventory(event):
    event.client.write(
        *utils.pretty_list(event.container.get_items_display())
    )


###############################################################################
# Shortcut
###############################################################################

def register_cmds(registry, admin=False):
    """
    Shortcut to register all standard item commands with default names
    """
    # Extend generic commands
    if 'look' not in registry:
        raise ValueError('Expected to find "look" command already registered')
    registry.extend('look', LookMixin)

    # Item-specific commands
    registry.register('inventory', cmd_inventory)


def register_aliases(registry):
    """
    Shortcut to register common aliases
    """
    registry.alias(r'^i$', cmd_inventory)
