"""
Registry for a data store
"""
from __future__ import unicode_literals

import copy
import os
import six

from .. import events


class Manager(object):
    # Flag for PostStart management
    _started = False

    def __init__(self):
        # Store class and server this manager is attached to
        # Set when StoreType metaclass calls our contribute_to_class
        self._store_cls = None
        self.service = None

        # Internal cache of active objects
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

        # Now know the service, we can hook up pre_start
        if self.service.server:
            # PreStart already fired
            self.pre_start()
        else:
            self.service.listen(events.PreStart, self.pre_start)

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
            self.service.settings.get_path('store_path'),
            self._store_cls._name,
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

    def pre_start(self, event=None):
        """
        Bound to the PreStart event by contribute_to_class (or if PreStart
        has already fired, it is called as soon as the manager is initialised)

        Lets stores take action if they were instantiated before the service
        was known, or before it had its settings (eg build filenames etc)
        """
        self._started = True
        for obj in self.cache.values():
            obj._pre_start(event)

    def get(self, keys):
        """
        Get a cached object. Similar to load(), but only returns from the
        cache.

        If a single key string is passed, the object matching the key will be
        returned, or None if it is not cached

        If a list of keys is passed, a dict keyed on object key will be
        returned; if an object is not cached, its value will be None.
        """
        if isinstance(keys, six.string_types):
            return self.cache.get(keys.lower())
        else:
            objs = {}
            for key in keys:
                key = key.lower()
                objs[key] = self.cache.get(key)
            return objs

    def load(self, keys, active=True):
        """
        Return one or more cached objects, or load one or more saved objects
        from disk.

        If a single key string is passed, the object matching the key will be
        returned, or None if it is not found.

        If a list of keys is passed, a dict keyed on object key will be
        returned; if an object does not exist, its value will be None.

        If active is True (by default), objects which are succesfully loaded
        will be added to the cache.
        """
        # Single key passed
        if isinstance(keys, six.string_types):
            key = keys.lower()

            # Check cache
            if key in self.cache:
                return self.cache[key]

            # Try to load from disk
            obj = self.store_cls(key, active=False)
            if obj.load():
                if active:
                    self.add_active(obj)
                return obj
            return None

        # Multiple keys
        else:
            objs = {}
            for key in keys:
                key = key.lower()

                # Check cache
                if key in self.cache:
                    objs[key] = self.cache[key]
                    continue

                # Load from disk
                obj = self.store_cls(key, active=False)
                if obj.load():
                    if active:
                        self.add_active(obj)
                else:
                    obj = None
                objs[key] = obj
            return objs

    def load_or_new(self, key, active=True):
        """
        Load an object from disk (or cache), or create it if it does not exist
        """
        obj = self.load(key, active)
        if not obj:
            obj = self.store_cls(key, active)
        return obj

    def add_active(self, obj):
        """
        Add an object to the active cache
        """
        self.cache[obj.key] = obj

    def remove_active(self, obj):
        """
        Remove an object from the active cache
        """
        if obj.key in self.cache:
            del self.cache[obj.key]

    def active(self):
        """
        Return objects which are active
        """
        return copy.copy(self.cache)

    def saved(self):
        """
        Return objects which are saved and not active
        """
        # Get list of keys who aren't active
        keys = []
        for filename in os.listdir(self.store_path):
            if not filename.endswith('.json'):
                continue
            key = filename[:-len('.json')]
            if key in self.cache:
                continue
            keys.append(key)
        return self.load(keys, active=False)

    def all(self):
        objs = self.saved()
        objs.update(self.active())
        return objs

    def serialise(self, session=True):
        """
        Serialise all active objects to dict

        Empties active objects
        """
        frozen = {}
        for key, obj in self.cache.items():
            frozen[key] = obj.to_dict(session=session)
        self.cache.clear()
        return frozen

    def deserialise(self, frozen, session=True):
        """
        Deserialise a serialised dict into active objects
        """
        for key, json in frozen.items():
            # Get from cache, in case it has already been referenced
            obj = self.load_or_new(key, active=True)
            obj.from_dict(json, session=session)
