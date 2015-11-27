"""
Mara storage fields
"""
import copy

from ..connection.client import Client, client_registry


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
            return self.default()
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
        """
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
        
        # Otherwise assume it's safe, or a subclass will know what to do
        return data
        
    def deserialise(self, obj, name, data):
        """
        Deserialise a serialised value onto the object
        """
        value = self.deserialise_value(data)
        self.set_value(obj, name, value)
    
    def set_value(self, obj, name, data):
        setattr(obj, name, data)
    
    def deserialise_value(obj, data):
        """
        Deserialise whatever was returned from serialise_data
        """
        if isinstance(data, dict):
            # Catch serialised objects
            if '__client__' in data:
                return client_registry.get(data['__client__'])
            
            return {
                self.deserialise_value(key): self.deserialise_value(value)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [self.deserialise_value(value) for value in data]
        
        # Otherwise assume it's unchanged
        return data



SFD_STORE = '_storefield_store_%s'
SFD_KEY = '_storefield_key_%s'
class StoreFieldDescriptor(object):
    """
    Descriptor to hold references to stores by store name and key, rather than
    by reference
    """
    def __init__(self, name):
        self.name = name
    
    def __get__(self, obj, type=None):
        # Find service
        if not hasattr(obj, 'service'):
            raise AttributeError('StoreField must be defined on a Store')
        service = obj.service
        
        # Collect reference from obj
        store_name = getattr(obj, SFD_STORE % self.name, None)
        key = getattr(obj, SFD_KEY % self.name, None)
        store = service.stores.get(store_name)
        if not store_name or not key or not store:
            # Either hasn't been set, or store no longer exists
            return None
        
        return store.manager.load(key)
        
    def __set__(self, obj, ref):
        setattr(obj, SFD_STORE % self.name, ref._name)
        setattr(obj, SFD_KEY % self.name, ref.key)
    
    def __delete__(self, obj):
        delattr(obj, SFD_STORE % self.name)
        delattr(obj, SFD_KEY % self.name)
        

def StoreField(Field):
    def contribute_to_class(self, store_cls, name):
        """
        Add a StoreFieldDescriptor to the object
        """
        setattr(store_cls, name, StoreFieldDescriptor(name))
    
    def serialise(self, obj, name):
        return {
            'store': getattr(obj, SFD_STORE % name, None),
            'key': getattr(obj, SFD_KEY % name, None),
        }
    
    def deserialise(self, obj, name, data):
        setattr(obj, SFD_STORE % name, data.get('store')),
        setattr(obj, SFD_KEY % name, data.get('key')),
