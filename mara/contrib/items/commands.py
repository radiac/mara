"""
Item-related commands
"""
from __future__ import unicode_literals

from .container import ItemContainerMixin
from .item import BaseItem
from .. import commands
from ... import events
from ... import util


###############################################################################
# Standard cmds
###############################################################################

class LookMixin(events.Handler):
    """
    Add this mixin to the cmd_look handler
    """
    def handler_01_init(self, event):
        self.items = None

    # Display items in this container
    def handler_50_find_items(self, event):
        if not isinstance(event.container, ItemContainerMixin):
            return
        self.items = event.container.get_items_display(depth=1, prose=True)

    def handler_55_display_items(self, event):
        if not self.items:
            return
        event.client.write('You can see %s' % util.pretty_list(self.items))


@commands.define_command(help="List items you are carrying")
class cmd_inventory(events.Handler):
    def handler_10_display(self, event):
        items = event.user.get_items_display(indent=2)
        if not items:
            event.client.write('You are holding nothing.')
            return
        event.client.write('You are holding:', *items)


@commands.define_command(
    args=r'^(?P<name>\w+)$', syntax="<item>",
    help="Examine an item",
)
class cmd_examine(events.Handler):
    def handler_01_init(self, event, name):
        self.items = None

    def handler_10_find_item(self, event, name):
        self.items = event.container.find_item(name)
        self.items.extend(event.user.find_item(name))

    def handler_20_examine(self, event, name):
        # ++ TODO: Move this logic into ItemContainerMixin.find_items
        if not self.items:
            event.client.write('Item not found')
        if len(self.items) > 1:
            event.client.write('Too many items found')

        event.client.write('You look at the %s' % name)
        event.client.write(self.items[0].description)


@commands.define_command(
    args=r'^(?P<item_type>\w+)?$', syntax="<item_type>",
    help="Create an item",
)
class cmd_create_item(events.Handler):
    def handler_10_find_cls(self, event, item_type=None):
        """
        Find item class from name provided
        """
        item_types = event.service.get_stores(BaseItem)

        # If no item specified, list available and stop
        if not item_type:
            if item_types:
                event.client.write('Available items:')
                for name, cls in item_types.items():
                    event.client.write('  %s' % name)
            else:
                event.client.write('No items available')
            event.stop()
            return

        # Find item class
        for name, cls in item_types.items():
            if name == item_type:
                self.item_cls = cls
                return
        event.client.write('No matching item found')
        event.stop()

    def handler_20_instantiate(self, event, item_type=None):
        """
        Create item
        """
        new_item = self.item_cls()
        event.user.add_item(new_item)
        event.client.write('Created %s' % self.item_cls.name)


###############################################################################
# Shortcut
###############################################################################

def register_cmds(registry, admin=False):
    """
    Shortcut to register all standard item commands with default names
    """
    if_admin = None
    if admin:
        from ..users.admin import if_admin

    # Extend generic commands
    if 'look' not in registry:
        raise ValueError('Expected to find "look" command already registered')
    registry.extend('look', LookMixin)

    # Item-specific commands
    registry.register('inventory', cmd_inventory)
    registry.register('examine', cmd_examine)

    # Admin commands
    registry.register('create_item', cmd_create_item, can=if_admin)


def register_aliases(registry):
    """
    Shortcut to register common aliases
    """
    registry.alias(r'^i$', 'inventory')
    registry.alias(r'^x(| .+)$', r'examine\1')
