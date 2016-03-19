from __future__ import unicode_literals

from mara.contrib.items import BaseItem

from .core import service


class Item(BaseItem):
    abstract = True
    service = service


class Brick(Item):
    name = 'brick'
    description = 'It is a red masonry brick'
