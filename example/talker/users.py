"""
Add user support to service

Must be imported before any events are bound
"""

from cletus.contrib.users import BaseUser
from cletus.contrib.users.password import PasswordMixin
from cletus.contrib.users.gender import GenderMixin

from .core import service

# Add user to client events
from cletus import events
from cletus.contrib.commands import CommandEvent
from cletus.contrib.users import event_add_user
service.listen(events.Connect, event_add_user)
service.listen(events.Disconnect, event_add_user)
service.listen(events.Receive, event_add_user)
service.listen(CommandEvent, event_add_user)

# Create User class
class User(PasswordMixin, GenderMixin, BaseUser):
    service = service


# Give client class a serialiser for the user attribute
from cletus.connection.client import ClientSerialiser

class UserSerialiser(ClientSerialiser):
    service = service
    
    def serialise(self, client, data):
        user = getattr(client, 'user', None)
        if user is None:
            return
        data['user'] = user.key
        
    def deserialise(self, client, data):
        user_key = data.get('user')
        user_store = self.service.stores.get('user')
        if user_key is None or user_store is None:
            return
        user = user_store.manager.load(user_key)
        user.client = client
        setattr(client, 'user', user)
