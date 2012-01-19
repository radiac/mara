"""
Storage, persistent and for sessions
"""

class Storable(object):
    """
    Abstract base class to implement store and session storage containers
    """
    def __init__(self):
        # User data which can be saved
        # Profile info, location data etc
        self._store = {}
        
        # User data which can't be saved
        # Game info etc
        self._session = {}
        
    def store(self, name):
        """
        Get a store dict
        """
        if not self._store.has_key(name):
            self._store[name] = {}
        return self._store[name]
    
    def session(self, name):
        """
        Get a session dict
        """
        if not self._session.has_key(name):
            self._session[name] = {}
        return self._session[name]
        