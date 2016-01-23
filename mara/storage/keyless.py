"""
Keyless session store
"""
from __future__ import unicode_literals

from .session import SessionManager, SessionStore

__all__ = ['KeylessManager', 'KeylessStore']

DISABLED_MSG = 'A keyless manager cannot perform lookups'


class KeylessManager(SessionManager):
    """
    A manager for a keyless session store
    """
    # Disable anything which depends on keys
    # Things which depend on persistence are disabled by SessionManager
    disabled_msg = DISABLED_MSG

    def get(self, keys):
        raise NotImplemented(self.disabled_msg)

    def add_active(self, obj):
        raise NotImplemented(self.disabled_msg)

    def remove_active(self, obj):
        raise NotImplemented(self.disabled_msg)

    # Don't complain when serialising, but we have nothing to serialise
    def serialise(self, session=True):
        return None

    def deserialise(self, frozen, session=True):
        return


class KeylessStore(SessionStore):
    """
    A session store which has no keys
    """
    abstract = True
    manager = KeylessManager()
    disabled_msg = DISABLED_MSG

    def __init__(self, **kwargs):
        """
        Initialise a keyless store

        Unlike a normal Store, does not accept key or active
        """
        if 'key' in kwargs:
            raise ValueError('KeylessStore does not accept "key" argument')
        if 'active' in kwargs:
            raise ValueError('KeylessStore does not accept "active" argument')

        super(KeylessStore, self).__init__('', active=False)
