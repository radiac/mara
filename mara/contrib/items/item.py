"""
Mara items
"""
from __future__ import unicode_literals

from .container import ItemContainerMixin
from .. import language
from ... import storage

__all__ = ["BaseItem"]


class BaseItem(storage.KeylessStore, ItemContainerMixin):
    """
    Item store
    """
    abstract = True

    #
    # Item attributes
    #

    # ItemContainer holding this object
    container = None

    # Name of the item - used for summaries and identifying objects
    # This should normally be a single noun, eg "sword"
    # This does not need to be unique - see _name and full_name
    name = None

    # Internal name of the item - used for serialisation.
    # Must be unique - clashes will raise a ValueError when defining the store.
    # This will normally be set automatically by the StoreType metaclass,
    # but can be set manually if you define multiple classes with the same
    # name, eg Sword and SwordOfOmens may both have the name "sword", but
    # set SwordOfOmens._name = "sword_omens"
    # _name =

    # Plural name of the item
    plural = property(lambda self: language.plural_noun(self.name))

    # Adjective, optional - used to generate default full_name
    adjective = None

    # Article for a single item ("a" or "an")
    article = property(lambda self: language.article_for_noun(self.name))

    # A description to show when examined
    description = 'It looks unremarkable'

    # If can_contain, this item can contain other objects
    can_contain = False

    # If fixed, it cannot be taken, dropped etc
    fixed = False

    # Full name - used for disambiguation
    # Normally built from adjective and name (eg "generic item", "red truck")
    # but can be set manually (eg "red truck with lights", "Sword of Omens")
    # on the class or instance
    @property
    def full_name(self):
        if not self.adjective:
            return self.name
        return '{} {}'.format(self.adjective, self.name)

    def __str__(self):
        return self.full_name

    def save(self):
        """
        Tells the parent container to save

        Although an item is keyless and session-only so cannot save itself, it
        will normally be held in an ItemContainer which can.
        """
        if self.container:
            self.container.save()
