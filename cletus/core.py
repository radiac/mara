"""
Cletus core
"""

import datetime
import time

from cletus.server import Server
from cletus.events import EventRegistry, Event
import cletus.log as log
from cletus.plugins import PluginRegistry
from cletus.storage import Storable
from cletus.user import User
import cletus.util as util

class Manager(Storable):
    """
    Abstract manager base class
    """
    def __init__(self, settings):
        # Initialise the store
        super(Manager, self).__init__()
        
        # Store settings
        self.settings = settings
        
        # Dict of users, client->user
        self._users = {}
        
        # No server to being with
        self.server = None
        
        # Consistent time for events
        self.time = time.time()
        
        # Initialise events
        self.events = EventRegistry(self)

        # Initialise plugin registry
        self.plugins = PluginRegistry(self)
        
    users = property(
        fget = lambda self: self._users.values(),
        doc = "Get a list of Users"
    )
    
    datetime = property(
        fget = lambda self: datetime.datetime.fromtimestamp(self.time),
        doc = "Get the current time as a datetime object"
    )
    
    
    #
    # Internal operations
    #
    
    def start(self):
        """
        Start the server
        """
        log.manager('Manager starting')
        
        # Load plugins
        self.plugins.load()

        # Start server
        self.server = Server(self)
        self.events.call('start')
        self.server.listen()
        
    def add_client(self, client):
        """
        A client has connected
        """
        user = User(self, client)
        self._users[client] = user
        self.events.call('connect', Event(user=user))
        
    def remove_client(self, client):
        """
        A client has disconnected
        """
        user = self._users[client]
        self.events.call('disconnect', Event(user=user))
        del self._users[client]

    def input(self, client, input):
        """
        A client has sent input
        """
        user = self._users[client]
        self.events.call('input', Event(
            user = user,
            input = input
        ))

    def poll(self):
        """
        A poll from the server
        """
        # Update time
        self.time = time.time()
        
        # Raise poll event
        self.events.call('poll')
    
    def reload(self):
        """
        Reset events and reload plugins
        """
        self.events.reset()
        self.plugins.load()

    def stop(self):
        """
        Stop the server
        """
        self.events.call('shutdown')
        self.server.shutdown()
        log.manager('Manager stopped')
