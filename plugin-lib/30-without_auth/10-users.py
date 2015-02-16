"""
Unauthenticated users for IRC-style chat
"""

from cletus.storage import Store, Field


class User(Store):
    """
    Store data about a user
    """
    # Unauthenticated users aren't saved
    can_save = False
    
    # Fields
    name        = Field(None)
    client      = Field(None)
    logged_in   = Field(False)
    debug       = Field(True)
    
    # Define regular expression for argument matching
    arg_match = '[a-zA-Z0-9]+'
    
    def __init__(self, name, client=None, logged_in=False):
        super(User, self).__init__()
        self.name = name
        self.client = client
        self.logged_in = logged_in
        
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
    
    def disconnect(self):
        """
        Disconnect the user
        """
        if not self.client:
            return
        self.client.close()
        self.client = None


class UserRegistry(Store):
    """
    User registry
    """
    # Unauthenticated users aren't saved
    can_save = False
    
    # Client -> User dict
    clients = Field({})
    
    # Name -> User dict
    # ++ If saving, save this
    names = Field({})
    
    def new_user(self, name, client, logged_in):
        user = User(name, client=client, logged_in=logged_in)
        self.clients[client] = user
        self.names[name] = user
        return user
    
    def logout(self, user):
        del self.clients[user.client]
        del self.names[user.name]
        
    def get_from_client(self, client):
        return self.clients.get(client, None)
    
    def get_from_name(self, name):
        return self.name.get(name, None)

manager.add_fields(
    users = Field(UserRegistry)
)


class UsernamePrompt(Prompt):
    message = 'Enter your name: '
    failed = message
    
    def validate(self, value):
        if not value.isalnum():
            self.client.write('Names must consist of only letters and numbers')
            return False
        
        for user in manager.users:
            if user.name == value:
                self.client.write('That name is already taken')
                return False
        return True
    
    def process(self, value):
        user = manager.users.new_user(value, self.client, logged_in=True)
        
        # Stop client from timing out
        user.client.timeout_time = 0
        
        # Send login event
        events.call('login', Event(user=user))
    



#
# Listeners
#

@listen('connect')
def connect(e):
    """
    Do something when the user connected
    """
    write(e.user, util.HR('Welcome to Cletus!'))
    manager.prompts[e.client] = UsernamePrompt(e.client)

@listen('login')
def welcome(e):
    # Announce and welcome
    write_all('-- %s has connected --' % e.user.name)
    list_users(e.user)
    
@listen('disconnect')
def disconnect(e):
    user = manager.get_from_client(e.client)
    if not user:
        return
    write_except(user, '-- %s has disconnected --' % user.name)
    events.call('logout', Event(
        user = user
    ))
    
    # Remove from users
    manager.users.logout(user)


#
# Commands
#

@command('name', args=[('name', str)])
def cmd_name(e):
    name = e.args.name
    if not user_name_validate(e.user, name):
        return
    write(e.user, 'Name changed to %s' % name)
    write_except(e.user, '-- %s changed their name to %s --' % (e.user.name, name))
    e.user.name = name
