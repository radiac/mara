"""
Cletus core
"""

from cletus.connect import Server
import cletus.log as log
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
        
        # Load plugins
        # ++
    
    
    #
    # Internal operations
    #
    
    def start(self):
        """
        Start the server
        """
        log.process('Manager starting')
        self.server = Server(self)
        self.server.listen()
        
    def add_user(self, user):
        """
        Add a user to the list of known users
        """
        self._users.append(user)
        self.user_connected(user)
        
    def remove_user(self, user):
        """
        Remove a user from the list of known users
        """
        self.user_disconnected(user)
        self._users.remove(user)
        
    def process(self, user, input):
        """
        Process user input
        """
        pass
        
    def stop(self):
        """
        Stop the server
        """
        self.server.shutdown()
        log.process('Manager stopped')
    
    def write_except(self, user, *lines):
        """
        Write something to everyone except the specified user
        """
        for other in users:
            if other == user:
                continue
            other.write(*lines)
    
    
    #
    # User interaction
    #
    
    def user_connected(self, user):
        """
        Do something when the user connected
        """
        user.write('Welcome!')
        user.prompt('Enter your name: ', self.user_named, self.user_name_validate)
    
    def user_name_validate(self, user, name):
        """
        Validate user's name
        """
        return name.isalnum()
    
    def user_named(self, user, name):
        """
        The user has responded to the name prompt
        """
        user.write('Hello, %s!' % name)
        user.name = name
        self.write_except(user, '-- %s has connected --')
    
    def user_disconnected(self, user):
        self.write_except(user, '-- %s has disconnected --')
        