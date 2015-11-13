"""
Data storage
"""

import json
import os

from .manager import Manager
from .fields import Field

__all__ = ['Store']

# List of reserved words for Store objects
RESERVED = [
    'service', 'abstract', 'manager',
    'to_dict', 'to_json', 'from_dict', 'from_json', 'save', 'load',
]


def str_to_filename(value):
    """
    Convert a string to a value safe to use as a filename
    """
    return "".join([
        c for c in value if c.isalpha() or c.isdigit() or c in '_-'
    ])

def is_filename_safe(value):
    """
    True if the string is safe to use as a filename
    """
    return value == str_to_filename(value)

class StoreType(type):
    """
    Store metaclass
    """
    def __new__(cls, name, bases, dct):
        """
        Create class
        """
        # Ensure name is safe for filesystem
        dct['_name'] = str_to_filename(name.lower())
        
        # Ensure abstract isn't inherited
        if not dct.get('abstract'):
            dct['abstract'] = False
        
        # Collect inherited Fields
        fields = {}
        for base in bases:
            if not hasattr(base, '_fields'):
                continue
            fields.update(base._fields)
        
        # Find new fields
        for field_name, field in dct.items():
            if not isinstance(field, Field):
                continue
            if field_name in RESERVED:
                raise ValueError('Forbidden field name "%s"' % field_name)
            fields[field_name] = field
        
        # See which fields can be saved and which cannot
        permanent_fields = []
        session_fields = []
        for field_name, field in fields.items():
            if field.session:
                session_fields.append(field_name)
            else:
                permanent_fields.append(field_name)
        
        # Create cls
        dct['_fields'] = fields
        dct['_permanent_fields'] = permanent_fields
        dct['_session_fields'] = session_fields
        return super(StoreType, cls).__new__(cls, name, bases, dct)
        
    def __init__(self, name, bases, dct):
        """
        Register class
        """
        super(StoreType, self).__init__(name, bases, dct)
        
        # If it's an abstract class, no further initialisation required
        if self.abstract:
            return
        
        # A non-abstract store needs a service
        if not self.service:
            raise ValueError('A store class must have a service')
        
        # Give fields an opportunity to manage how they're added to the class
        for field_name, field in self._fields.items():
            field.contribute_to_class(self, field_name)
        
        # Register with the service's registry, ensure there's only one
        if self._name in self.service.stores:
            raise ValueError(
                'Store with name %s already defined' % self._name
            )
        self.service.stores[self._name] = self
    
        # Give the manager instance a reference to the store
        if isinstance(self.manager, Manager):
            self.manager.contribute_to_class(self)
        else:    
            raise ValueError('Store manager must be a Manager instance')
        

class Store(object):
    """
    Abstract base class to implement session and stored data
    """
    __metaclass__ = StoreType
    
    # Service this store class is linked to
    # Must be set by subclass
    service = None
    
    # If abstract, is not added to registry
    abstract = True
    
    # The manager for this store
    manager = Manager()
    
    # Internal variables added by metaclass:
    #   _name               Name of the store (used in path)
    #   _filename           Filename for the store
    #   _fields             Dict of field instance lookups
    #   _permanent_fields   List of names of fields which can be saved
    #   _session_fields     List of names of fields which cannot be saved
    
    def __init__(self, key, active=True):
        """
        Initialise a stored object
        """
        key = key.lower()
        if not is_filename_safe(key):
            raise ValueError('Key is not safe for filename')
        self.key = key
        self._filename = os.path.join(
            self.manager.store_path, "%s.json" % self.key
        )
        
        # Tell fields to initialise themselves
        for field_name, field in self._fields.items():
            field.contribute_to_instance(self, field_name)
        
        # Ensure manager knows about it
        if active:
            self.manager.add_active(self)
        
    def to_dict(self, session=False):
        """
        Create data dict from instance data, suitable for json.dumps
        
        To override how a field is frozen, define a method freeze_<fieldname>
        
        If session=True, include temporary session data
        """
        # Iterate through self.saved and put into data object
        data = {}
        for name in self._permanent_fields if not session else self.fields.keys():
            data[name] = getattr(self, name)
        return data
    
    def from_dict(self, data, session=False):
        """
        Create new instance with data dict from to_dict()
        
        To override how a field is thawed, define a method thaw_<fieldname>
        """
        for name in self._permanent_fields if not session else self.fields.keys():
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
            return json.dumps(data, cls=JSONEncoderFactory(self.service, session))
        except Exception, e:
            self.service.log.store('Cannot save to string: %s' % e)
            return ''
        
    def from_json(self, raw, session=False):
        """
        Load data from a JSON string
        """
        try:
            data = json.loads(raw, cls=JSONDecoderFactory(self.service, session))
            self.from_dict(data)
        except Exception, e:
            self.service.log.store('Cannot load from string: %s' % e)
        
    def save(self):
        """
        Save stored data to disk
        """
        # Ensure store path exists
        store_path = self.manager.store_path
        if not os.path.exists(store_path):
            os.makedirs(store_path)
        
        # Get filepath
        filename = self._filename
        
        # Write into file
        raw = self.to_json()
        self.service.log.store('Saving %s' % filename)
        f = open(filename, 'w')
        f.write(raw)
        f.close()

    def load(self):
        """
        Load stored data from disk
        
        Returns True if loaded, False if not
        """
        filename = self._filename
        if not os.path.exists(filename):
            self.service.log.store('Cannot load %s, does not exist' % filename)
            return False
        
        # Read from file
        self.service.log.store('Loading %s' % filename)
        f = open(filename, 'r')
        raw = f.read()
        f.close()
        
        self.from_json(raw)
        return True


def JSONDecoderFactory(service, session=False):
    class StorageJSONDecoder(json.JSONDecoder):
        def decode(self, raw):
            decoded = super(StorageJSONDecoder, self).decode(raw)
            if '__store__' in decoded:
                cls = service.stores.get(decoded['__store__'])
                del decoded['__store__']
                if cls is not None:
                    store = cls()
                    store.from_dict(decoded, session)
                return None
            return decoded
        
        
def JSONEncoderFactory(service, session=False):
    class StorageJSONEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, Store):
                obj = obj.to_dict(session)
                obj['__store__'] = obj._name
            
            return super(StorageJSONEncoder, self).default(obj)


class TempStoreMixin(object):
    """
    A mixin to disable saving and loading for a store
    """
    def save(self):
        return
    def load(self):
        return False
