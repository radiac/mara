"""
Cletus storage fields
"""
import copy

class Field(object):
    """
    Field for a Store
    
    Default can be a callable, eg a function or class, which will be
    instantiated for each new Store instance
    
    A single Field instance should expect to be used by multiple Store classes,
    so should not hold data specific to a store. If a field needs to hold such
    data, it could hold it on the store class itself, in a bound descriptor,
    or use contribute_to_class to create a copy of itself (depending on the
    scope and complexity of the data).
    """
    def __init__(self, default=None, session=False):
        self._default = default
        self.session = session
     
    def contribute_to_class(self, store_cls, name):
        """
        Called when the store class is created
        
        Give fields the opportunity to define themselves on the class.
        
        Used by complex fields to set a descriptor.
        """
        pass
        
    def contribute_to_instance(self, store_cls, name):
        """
        Called when the store class is created
        
        Give fields the opportunity to define themselves on the instance.
        
        Used by simple fields to set the value to the default value.
        """
        setattr(store_cls, name, self.default)
    
    def get_default(self):
        if callable(self._default):
            return self.default()
        return copy.copy(self._default)
    default = property(get_default)
