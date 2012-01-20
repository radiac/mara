"""
User management
"""

import socket

from cletus.storage import Storable

class User(Storable):
    """
    Manage a client
    """
    # Define regular expression for argument matching
    arg_match = '[a-zA-Z0-9]+'
    
    def __init__(self, manager, client=None):
        # Initialise the store
        super(User, self).__init__()
        self.store('profile').update({
            'name': None,
            'debug': True
        })
        
        # Store vars
        self.manager = manager;
        self.client = client
        self.settings = self.manager.settings;
        
        # State
        self.logged_in = False
        
    def write(self, *lines):
        """
        Send complete lines of data to the user
        """
        if not self.client:
            return
        self.client.write(*lines)
    
    def write_raw(self, raw):
        """
        Send raw data to the user
        """
        if not self.client:
            return
        self.client.write_raw(raw)
    
    # Name is going to be common to almost all use-cases - make it easy to access
    name = property(
        fget = lambda self: self.store('profile')['name'],
        fset = lambda self, name: self.store('profile').__setitem__('name', name),
        doc = 'Get or set the user name'
    )
    
    def disconnect(self):
        """
        Disconnect the user
        """
        if not self.client:
            return
        self.client.close()
        self.client = None
        