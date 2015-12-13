"""
Yaml instantiator
"""
from __future__ import absolute_import
from collections import defaultdict

import yaml

def instantiate(service, path):
    """
    Given a service and path to a yaml file, load the file and use its
    documents to instantiate stores
    
    Returns instantiated stores as {store_name: {key: store, ...}, ...}
    """
    f = open(path, 'r')
    docs = yaml.load_all(f)
    loaded = defaultdict(dict)
    for doc in docs:
        # Get store
        if 'store' not in doc:
            raise TypeError('Yaml store class unknown in doc %s' % doc)
        store_name = doc.pop('store')
        store = service.stores.get(store_name)
        if not store:
            raise ValueError('Unknown store type "%s"' % doc['store'])
        
        if 'key' not in doc:
            raise TypeError('Yaml store missing key in doc %s' % doc)
        key = doc.pop('key')
        
        # Now instantiate the object
        loaded[store_name][key] = store(key, active=True, **doc)
    f.close()
    return loaded
