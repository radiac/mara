"""
Mara storage fields
"""
from __future__ import unicode_literals

import copy

from ..connection.client import Client, client_registry

__all__ = ['Field']


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
        if isinstance(getattr(store_cls, name), Field):
            setattr(store_cls, name, self.default)
    
    def get_default(self):
        if callable(self._default):
            return self._default()
        return copy.copy(self._default)
    default = property(get_default)

    def serialise(self, obj, name):
        """
        Prepare a value for serialisation in a dict to send to another process,
        or save as a json string
        """
        return self.serialise_value(self.get_value(obj, name))
    
    def get_value(self, obj, name):
        return getattr(obj, name)
        
    def serialise_value(self, data):
        """
        Make sure that objects are serialised safely
        * Serialises dict keys and values
        * Serialises list and tuple values into lists
        * Serialises Client objects
        * Serialises KeylessStore objects in-place
        * Stores key references to Store and SessionStore objects
          (their own managers control their data serialisation)
        """
        from .store import Store
        from .keyless import KeylessStore
        
        if isinstance(data, dict):
            return {
                self.serialise_value(key): self.serialise_value(value)
                for key, value in data.items()
            }
            
        elif isinstance(data, list):
            # No duck typing here - we need to deserialise exactly
            return [self.serialise_value(value) for value in data]
            
        elif isinstance(data, Client):
            return {'__client__': data.id}
            
        elif isinstance(data, KeylessStore):
            # KeylessStore is serialised here and only here
            return {
                '__store__': data._name,
                '__keyless__': data.to_dict(session=session)
            }
            
        elif isinstance(data, Store):
            # Store (and SessionStore) is serialised by their manager,
            # so just store key
            return {
                '__store__': data._name,
                'key': data.key,
            }
        
        # Otherwise assume it's safe, or a subclass will know what to do
        return data
        
    def deserialise(self, obj, name, data):
        """
        Deserialise a serialised value onto the object
        """
        value = self.deserialise_value(obj, data)
        self.set_value(obj, name, value)
    
    def set_value(self, obj, name, data):
        setattr(obj, name, data)
    
    def deserialise_value(self, obj, data):
        """
        Deserialise whatever was returned from serialise_data
        """
        if isinstance(data, dict):
            # Catch serialised objects
            if '__client__' in data:
                return client_registry.get(data['__client__'])
                
            elif '__store__' in data:
                # Find the object; if it hasn't been deserialised yet it should
                # be in a moment
                store = obj.service.stores.get(data['__store__'])
                if not store:
                    return None
                if '__keyless__' in data:
                    # No key, instantiate store here
                    return store(**data['__keyless__'])
                else:
                    # Load by key from store or cache
                    return store.manager.load_or_new(data['key'])
                
            return {
                self.deserialise_value(obj, key):
                self.deserialise_value(obj, value)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [self.deserialise_value(obj, value) for value in data]
        
        # Otherwise assume it's unchanged
        return data
