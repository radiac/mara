"""
Keyless session store
"""
from __future__ import unicode_literals

from .manager import Manager
from .storage import Store

__all__ = ['SessionManager', 'SessionStore']

DISABLED_MSG = 'A session manager cannot provide persistence'


class SessionManager(Manager):
    """
    A manager for a keyless session store
    """
    # Disable anything which depends on persistence
    disabled_msg = DISABLED_MSG
    
    def load(self, keys, active=True):
        raise NotImplemented(self.disabled_msg)
    
    def load_or_new(self, key, active=True):
        """Always create a new object"""
        return self.new(key, active)
        
    def saved(self, obj):
        raise NotImplemented(self.disabled_msg)
    
    def remove_active(self, obj):
        raise NotImplemented(self.disabled_msg)


class SessionStore(Store):
    """
    A session-only store, where saving and loading is disabled
    """
    abstract = True
    manager = SessionManager()
    disabled_msg = DISABLED_MSG
    
    def save(self):
        raise NotImplemented(self.disabled_msg)
    
    def load(self):
        raise NotImplemented(self.disabled_msg)
