"""
Cletus core
"""

from cletus.connection import Server
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
        log.manager('Manager starting')
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
        
    def stop(self):
        """
        Stop the server
        """
        self.server.shutdown()
        log.manager('Manager stopped')
    
    
    #
    # Polling
    #
    
    def poll(self):
        """
        A poll from the server
        """
        pass
        
        
    #
    # User management
    #
    
    def find_others(self, target):
        """
        Get a list of users who are visible to the specified user
        Excludes the specified user
        """
        return [user for user in self._users if user.name and user != target]
        
    def write_all(self, *lines):
        """
        Write something to everyone who has logged on
        """
        for user in self._users:
            if user.name:
                user.write(*lines)
        
    def write_except(self, target, *lines):
        """
        Write something to everyone except the specified user
        """
        for user in self._users:
            if user == target or not user.name:
                continue
            user.write(*lines)
    
    
    #
    # User interaction
    #
    
    def process(self, user, input):
        """
        Process user input
        """
        if input:
            self.write_all("%s: %s" % (user.name, input))
        
    def user_connected(self, target):
        """
        Do something when the user connected
        """
        target.write('-- Welcome to Cletus --')
        target.prompt('Enter your name: ', self.user_named, self.user_name_validate)
    
    def user_name_validate(self, target, name):
        """
        Validate user's name
        """
        if not name.isalnum():
            target.write('Names must consist of only letters and numbers')
            return False
        
        for user in self._users:
            if user.name == name:
                target.write('That name is already taken')
                return False
        return True
    
    def user_named(self, user, name):
        """
        The user has responded to the name prompt
        """
        # Store
        user.name = name

        # Announce
        self.write_all('-- %s has connected --' % user.name)
        
        # Look
        others = self.find_others(user)
        if len(others) == 1:
            user.write('Also here: %s' % ', '.join([o.name for o in others]))
        else:
            user.write('Nobody else is here.')
        
    
    def user_disconnected(self, user):
        self.write_except(user, '-- %s has disconnected --' % user.name)
        