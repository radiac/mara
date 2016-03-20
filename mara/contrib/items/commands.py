"""
Item-related commands
"""
from __future__ import unicode_literals

from .container import ItemContainerMixin
from .item import BaseItem
from .. import commands
from .. import language
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


class ItemActionHandler(events.Handler):
    """
    A command handler base class for commands which take an item's name
    * Finds the item(s) at handler_10, validates at handler_20
    * Handles no item found, or ambiguous match
    * Sets them on self.items
    """
    # Argument pattern and syntax
    # ++ TODO: Add support for resolving ambiguous matches
    # ++ Note: Subclasses should expect arguments to change in future versions
    arg_pattern = r'^(?P<name>\w+)$'
    arg_syntax = "<item>"

    # If recurse=True, will check items within items within items
    # Can also be set to a number to specify how many levels deep to go
    recurse = False

    def handler_10_find(self, event, name):
        self.in_container = event.container.find_items(
            name, recurse=self.recurse,
        )
        self.in_user = event.user.find_items(name, recurse=self.recurse)
        self.items = self.in_container + self.in_user

    def handler_20_validate(self, event, name):
        # ++ TODO: Support for flagging ambiguous matches
        if not self.items:
            event.client.write('You cannot find %s %s' % (
                language.article_for_noun(name), name,
            ))
            event.stop()


@commands.define_command(
    args=ItemActionHandler.arg_pattern, syntax=ItemActionHandler.arg_syntax,
    help="Examine an item",
)
class cmd_examine(ItemActionHandler):
    def handler_50_examine(self, event, name):
        item = self.items[0]
        event.client.write('You look at the %s' % item.full_name)
        event.client.write(item.description)


@commands.define_command(
    args=ItemActionHandler.arg_pattern, syntax=ItemActionHandler.arg_syntax,
    help="Drop an item",
)
class cmd_drop(ItemActionHandler):
    def handler_30_user_only(self, event, name):
        if not self.in_user:
            event.client.write('You are not holding the %s' % name)
            event.stop()
        self.items = self.in_user

    def handler_50_drop(self, event, name):
        item = self.items[0]
        event.client.write('You drop the %s' % item.name)
        item.container.remove_item(item)
        event.container.add_item(item)


@commands.define_command(
    args=ItemActionHandler.arg_pattern, syntax=ItemActionHandler.arg_syntax,
    help="Take an item",
)
class cmd_take(ItemActionHandler):
    def handler_30_container_only(self, event, name):
        if not self.in_container:
            event.client.write('You are already holding the %s' % name)
            event.stop()

    def handler_50_drop(self, event, name):
        item = self.items[0]
        if item.fixed:
            event.client.write('You cannot take the %s' % item.name)
            event.stop()
            return

        event.client.write('You take the %s' % item.name)
        item.container.remove_item(item)
        event.user.add_item(item)


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


@commands.define_command(
    args=ItemActionHandler.arg_pattern, syntax=ItemActionHandler.arg_syntax,
    help="Destroy an item",
)
class cmd_destroy_item(ItemActionHandler):
    def handler_50_destroy(self, event, name):
        item = self.items[0]
        item.container.remove_item(item)
        event.client.write('Removed %s' % item.name)


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
    registry.register('drop', cmd_drop)
    registry.register('take', cmd_take)

    # Admin commands
    registry.register('create_item', cmd_create_item, can=if_admin)
    registry.register('destroy_item', cmd_destroy_item, can=if_admin)


def register_aliases(registry):
    """
    Shortcut to register common aliases
    """
    registry.alias(r'^i$', 'inventory')
    registry.alias(r'^x(| .+)$', r'examine\1')
