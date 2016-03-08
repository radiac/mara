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

    # Name of the item
    name = 'generic item'

    # Plural name of the item
    plural = property(lambda self: language.plural_noun(self.name))

    # Article for a single item
    article = property(lambda self: language.article_for_noun(self.name))

    # A description to show when examined
    description = 'It looks fairly generic'

    # If fixed, it cannot be taken, dropped etc
    fixed = True

    def save(self):
        """
        Tells the parent container to save

        Although an item is keyless and session-only so cannot save itself, it
        will normally be held in an ItemContainer which can.
        """
        if self.container:
            self.container.save()
