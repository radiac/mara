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

    def serialise(self, obj, name):
        """
        Prepare a value for serialisation in a dict or json string
        """
        return getattr(obj, name)
    
    def deserialise(self, obj, name, data):
        """
        Deserialise a serialised value onto the object
        """
        setattr(obj, name, data)


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
    def contribute_to_instance(self, store_cls, name):
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
