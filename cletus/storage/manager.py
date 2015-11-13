"""
Registry for a data store
"""

import copy
import os


class Manager(object):
    def __init__(self):
        self._store_cls = None
        self.service = None
        self.cache = {}
    
    @property
    def store_cls(self):
        """
        The Store class of this manager
        """
        return self._store_cls
    
    @store_cls.setter
    def store_cls(self, store_cls):
        """
        Set the store class and collect data from it to populate internal
        variables
        """
        self._store_cls = store_cls
        self.service = store_cls.service
    
    @property
    def store_path(self):
        """
        The filesystem path for this Store
        
        Has to be generated at runtime, as settings will not be known when
        store class is defined.
        """
        if not self.service:
            return None
        return os.path.join(
            self.service.settings.store_path, self._store_cls._name,
        )
    
    def __copy__(self):
        return self.__class__()
        
    def contribute_to_class(self, store_cls):
        """
        Called when a Store class is created
        
        This is responsible for ensuring that the store has a manager which
        isn't shared by any base classes of the store.
        """
        new_manager = copy.copy(self)
        new_manager.store_cls = store_cls
        setattr(store_cls, 'manager', new_manager)
    
    def load(self, keys):
        """
        Return one or more cached objects, or load one or more saved objects
        from disk.
        
        If a single key string is passed, the object matching the key will be
        returned, or None if it is not found.
        
        If a list of keys is passed, a dict keyed on object key will be
        returned; if an object does not exist, its value will be None.
        """
        # Single key passed
        if isinstance(keys, basestring):
            key = keys.lower()
            
            # Check cache
            if key in self.cache:
                return self.cache[key]
            
            # Try to load from disk
            obj = self.store_cls(key, active=False)
            if obj.load():
                self.add_active(obj)
                return obj
            return None
            
        # Multiple keys
        else:
            objs = {}
            for key in keys:
                key = key.lower()
                
                # Check cache
                if keys in self.cache:
                    objs[key] = self.cache[key]
                    continue
                
                # Load from disk
                obj = self.store_cls(key, active=False)
                if obj.load():
                    self.add_active(obj)
                else:
                    obj = None
                objs[key] = obj
            return objs
                
    def add_active(self, obj):
        """
        Add an object to the active cache
        """
        self.cache[obj.key] = obj
    
    def remove_active(self, obj):
        """
        Remove an object from the active cache
        """
        del self.cache[obj.key]
    
    def active(self):
        return copy.copy(self.cache)
    
    def saved(self):
        # Get list of keys
        keys = []
        for filename in os.listdir(self.store_path):
            if not filename.endswith('.json'):
                continue
            keys.append(filename[:len('.json')])
        return self.load(keys, active=False)
        
    def all(self):
        objs = self.saved()
        objs.update(self.active())
        return objs
