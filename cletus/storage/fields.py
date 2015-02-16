"""
Cletus storage fields
"""
import copy

class Field(object):
    """
    Field for a Store
    
    Default can be a callable, eg a function or class, which will be
    instantiated for each new Store instance
    """
    name = None
    def __init__(self, default=None, save=False):
        self._default = default
        self.value = default
        self.save = save
    
    def init_store(self, store, name):
        """
        Called when a store instance is created
        """
        setattr(store, name, self.default)
    
    def get_default(self):
        if callable(self._default):
            return self.default()
        return copy.copy(self._default)
    default = property(get_default)
