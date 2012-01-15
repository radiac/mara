"""
Cletus core
"""

from cletus.connection import Server
from cletus.events import EventRegistry, Event
import cletus.log as log
from cletus.plugins import PluginRegistry
import cletus.util as util

class Manager(object):
    """
    Abstract manager base class
    """
    def __init__(self, settings):
        self.settings = settings
        
        # List of users
        self._users = []
        self.server = None
        
        # Initialise events
        self.events = EventRegistry(self)

        # Initialise plugin registry
        self.plugins = PluginRegistry(self)
    

    users = property(
        fget = lambda self: self._users,
        doc = "Get a list of Users"
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
        
    def add_user(self, user):
        """
        Add a user to the list of known users
        """
        self._users.append(user)
        self.events.call('connect', Event(user=user))
        
    def remove_user(self, user):
        """
        Remove a user from the list of known users
        """
        self.events.call('disconnect', Event(user=user))
        self._users.remove(user)

    def input(self, user, input):
        """
        Process user input
        """
        self.events.call('input', Event(
            user = user,
            input = input
        ))

    def poll(self):
        """
        A poll from the server
        """
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
