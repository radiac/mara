"""
Data storage
"""

import json
import os

from .fields import Field

__all__ = ['Store']


# Storage registry to ensure no two stores have the same name
registry = {}


class StoreType(type):
    """
    Store metaclass
    """
    def __new__(cls, name, bases, dct):
        """
        Create class
        """
        if not dct.get('_abstract'):
            dct['_abstract'] = False
            if name in registry:
                raise ValueError('Store with name %s already defined' % name)
        dct['_store_name'] = name
        
        # Prepare Field class attributes
        fields = {}
        for field_name, field in dct.items():
            if not isinstance(field, Field):
                continue
            fields[field_name] = field
        
        # See which fields can be saved and which cannot
        saved_fields = []
        session_fields = []
        for field_name, field in fields.items():
            if field.save:
                saved_fields.append(field_name)
            else:
                session_fields.append(field_name)
        
        # Create cls
        dct['_fields'] = fields
        dct['_saved_fields'] = saved_fields
        dct['_sesssion_fields'] = session_fields
        return super(StoreType, cls).__new__(cls, name, bases, dct)
        
    def __init__(self, name, bases, dct):
        """
        Register class with registry
        """
        super(StoreType, self).__init__(name, bases, dct)
        if not self._abstract:
            registry[name] = self


class Store(object):
    """
    Abstract base class to implement session and stored data
    """
    __metaclass__ = StoreType
    # Variables added by metaclass:
    #   _store_name         Name of the store (used in path)
    #   _fields             Dict of field instance lookups
    #   _saved_fields       List of names of fields which can be saved
    #   _session_fields     List of names of fields which cannot be saved
    
    # If abstract, is not added to registry
    _abstract = True
    
    # If False, load() and save() will do nothing
    _can_save = False
    
    def __init__(self, service, key):
        """
        Initialise a store
        
        This should not be called directly - instead call service.store()
        """
        self.service = service
        self.key = key
        
        # Tell fields to initialise themselves as values
        for field_name, field in self._fields:
            field.init_store(self, field_name)
        
    def _get_store_path(self):
        return os.path.join(self.service.settings.store, self._store_name)
    
    def _get_store_filename(self):
        "Get full path to store file"
        return os.path.join(
            self._get_store_path(), "%s.json" % self.key
        )
        
    def to_dict(self, session=False):
        """
        Create data dict from instance data, suitable for json.dumps
        
        To override how a field is frozen, define a method freeze_<fieldname>
        """
        # Iterate through self.saved and put into data object
        data = {}
        for name in self.saved_fields if not session else self.fields.keys():
            data[name] = getattr(self, name)
        return data
    
    def from_dict(self, data, session=False):
        """
        Create new instance with data dict from to_dict()
        
        To override how a field is thawed, define a method thaw_<fieldname>
        """
        for name in self.saved_fields if not session else self.fields.keys():
            # Check if Field has been added since it was saved - leave default
            if name not in data:
                continue
            setattr(self, name, data[name])
        return self
    
    def to_json(self, session=False):
        """
        Save data to a JSON string
        """
        try:
            data = self.to_dict()
            return json.dumps(data, cls=JSONEncoderFactory())
        except Exception, e:
            self.service.log.store('Cannot save to string: %s' % e)
            return ''
        
    def from_json(self, raw, session=False):
        """
        Load data from a JSON string
        """
        try:
            data = json.loads(raw, cls=JSONDecoderFactory(session))
            self.from_dict(data)
        except Exception, e:
            self.service.log.store('Cannot load from string: %s' % e)
        
    def save(self):
        """
        Save stored data to disk
        """
        if not self._can_save:
            return
        
        # Ensure store path exists
        store_path = self._get_store_path()
        if not os.path.exists(store_path):
            os.makedirs(store_path)
        
        # Get filepath
        filename = self._get_store_filename()
        
        # Write into file
        raw = self.to_json()
        self.service.log.store('Saving %s' % filename)
        f = open(filename, 'w')
        f.write(raw)
        f.close()

    def load(self):
        """
        Load stored data from disk
        """
        if not self._can_save:
            return
        
        filename = self._get_store_filename()
        if not os.path.exists(filename):
            self.service.log.store('Cannot load %s, does not exist' % filename)
            return
        
        # Read from file
        self.service.log.store('Loading %s' % filename)
        f = open(filename, 'r')
        raw = f.read()
        f.close()
        
        self.from_json(raw)


def JSONDecoderFactory(session=False):
    class StorageJSONDecoder(json.JSONDecoder):
        def decode(self, s):
            decoded = super(StorageJSONDecoder, self).decode(s)
            if '__store__' in decoded:
                cls = registry.get(decoded['__store__'])
                del decoded['__store__']
                if cls is not None:
                    store = cls()
                    store.from_dict(decoded, session)
                return None
            return decoded
        
        
def JSONEncoderFactory(session=False):
    class StorageJSONEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, Store):
                o = o.to_dict(session)
                o['__store__'] = o.name
            
            return super(StorageJSONEncoder, self).default(o)

