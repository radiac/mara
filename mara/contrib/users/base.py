"""
Mara users
"""

from ..commands import define_command
from ...connection.client import ClientSerialiser
from ... import events
from ... import storage
from ... import util


def event_add_user(event):
    """
    Add user object to events (when available)
    """
    event.user = getattr(event.client, 'user', None)


class ClientField(storage.Field):
    """
    The client attribute is special - it will be assigned by the client's
    UserSerialiser
    """
    def serialise(self, obj, name):
        return None
    

class UserManager(storage.Manager):
    def get_active_by_name(self, names):
        active = self.active()
        lower_names = [name.lower() for name in names]
        found = { k: v for k, v in active.items() if k in lower_names }
        missing = set(lower_names).difference(set(found.keys()))
        if missing:
            raise ValueError(
                'Unknown users %s' % util.pretty_list(list(missing))
            )
        return found


class BaseUser(storage.Store):
    abstract = True
    manager = UserManager()
    
    client = ClientField(session=True)
    name = storage.Field('')
    
    def write(self, *lines):
        self.client.write(*lines)
    
    def disconnect(self):
        """
        Call to disconnect the user
        """
        # Tell the client to close
        self.client.close()
        
    def disconnected(self):
        """
        Clean up User object when a user disconnects
        """
        # Manually break circular reference for efficient garbage collection
        self.client = None
        
        # Remove from active list
        self.manager.remove_active(self)


@define_command(help='List all users')
def cmd_list_users(event):
    """
    List admin users
    
    Needs the user class in context as: context={'User': User}
    """
    User = event.context['User']
    
    online = [user.name for user in sorted(User.manager.active().values())]
    offline = [user.name for user in sorted(User.manager.saved().values())]
    event.user.write(
        util.HR('Users'),
        'Online: ' + util.pretty_list(online),
        'Offline: ' + util.pretty_list(offline),
        util.HR(),
    )

# Give client class a serialiser for the user attribute
class BaseUserSerialiser(ClientSerialiser):
    """
    Client serialiser to persist user object across reboots
    
    Subclasses must set two attributes:
    
        store_name      The name of the user store
        attr            The name of the client that holds the user object
    """
    abstract = True
    store_name = None
    attr = None
    
    def serialise(self, client, data):
        user = getattr(client, self.attr, None)
        if user is None:
            return
        data[self.attr] = user.key
        
    def deserialise(self, client, data):
        user_key = data.get(self.attr)
        user_store = self.service.stores.get(self.store_name)
        if user_key is None or user_store is None:
            return
        user = user_store.manager.load(user_key)
        user.client = client
        setattr(client, self.attr, user)
