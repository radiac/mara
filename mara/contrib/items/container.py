"""
Container mixin for stores which hold items
"""
from __future__ import unicode_literals

from collections import Counter
import six

from ... import storage

__all__ = ['ItemContainerMixin']


class ItemContainerMixin(storage.Store):
    """
    Mixin for a store so it can contain items
    """
    # List of items
    items = storage.Field(list)
    
    def add_item(self, item):
        self.items.append(item)
        self.save()
    
    def remove_item(self, item):
        self.items.remove(item)
        self.save()
    
    def get_items_display(
        self, filter_cls=None, depth=0, indent=0, indent_size=0,
    ):
        """
        Return a list of formatted and nested item strings suitable to display,
        optionally filtered by issubclass, and optionally recurse any container
        items and list their children too.
        
        If an item is recursed, its entry in the returned list will be a tuple
        of (item, children), where children is a list of items and tuples of
        deeper containers.
        
        If the container holds more than one item with the same string value,
        they will be counted together, eg "3 red balloons".
        
        Arguments:
            filter_cls
                Only return items that are subclasses of this
                (argument used directly in issubclass).
                
                Default: None
                            
            depth
                Depth of any child items to list, with 0 meaning no children,
                1 direct descendants, 2 children and grandchildren etc.
                
                Use a negative depth to list all descendants without limit.
                
                Default: 0 (no children)
            
            indent
                Number of space characters to start this line with. Used
                internally when recursing, but can be used to give an indent to
                the top level of items.
                
                Default: 0
            
            indent_size
                Size of each indent, in characters.
                
                Default: 2
        """
        
        # ++ Ah. This won't work so good with things that contain things
        # ++ Also, this will work on instance ref, so everthin will be 1.
        # ++ Need to step through sorted list of items, build a string/list for
        # ++ each item, then compare it to the previous (if exists); if it
        # ++ matches, there are two, increase the item's count. If it doesn't,
        # ++ add new item
        # ++ Therefore build into a list of (item_strings:list, count) in the
        # ++ first loop, then unbundle that into strings in a comprehension
        
        # Sort items by their text value
        items = sorted(self.items, key=lambda i: six.text_type(i))
        
        # Make list of text lines
        lines = []
        for item in items:
            # Filter by class
            if filter_cls and not issubclass(item, filter_cls):
                continue
            
            # Recurse containers to specified depth
            children = None
            if depth != 0 and issubclass(item, ItemContainerMixin):
                children = item.get_items(
                    filter_cls=filter_cls, depth=depth - 1,
                    indent=indent + indent_size, indent_size=indent_size,
                )
            
            # Now store as a tuple
            items.append(six.text_type(item), children)
        
        # Now we've got strings for each item
        item_str = '%s%s' % (' ' * indent, item)
        counter = Counter(self.items)
        for item, count in sorted(zip(counter.keys(), counter.values())):
            # Filter by class
            if filter_cls and not issubclass(item, filter_cls):
                continue
            
            # Recurse containers to specified depth
            if depth != 0 and issubclass(item, ItemContainerMixin):
                lines.extend(
                    item.get_items(
                        filter_cls=filter_cls, depth=depth - 1,
                        indent=indent + indent_size, indent_size=indent_size,
                    )
                )
            else:
                lines.append('%s%s' % (' ' * indent, item))
        return lines
