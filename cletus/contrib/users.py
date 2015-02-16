"""
Cletus users
"""
from .commands import command
from ... import storage
from ... import util


class User(storage.Store):
    client = storage.Field(None)
    name = storage.Field('', save=True)

    def write(self, *lines):
        self.client.write(*lines)
