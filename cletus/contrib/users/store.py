"""
Cletus users
"""
from ..commands import command
from ... import events
from ... import storage
from ... import util


def event_add_user(event):
    """
    Add user object to events (when available)
    """
    event.user = getattr(event.client, 'user', None)


class UserManager(storage.Manager):
    def get_active_by_name(self, names):
        active = self.active()
        lower_names = [name.lower() for name in names]
        found = { k: v for k, v in active.items() if k in lower_names }
        missing = set(lower_names).difference(set(found.keys()))
        if missing:
            raise ValueError('Unknown users %s' % util.pretty_list(missing))
        return found


class UserBase(storage.Store):
    abstract = True
    manager = UserManager()
    
    client = storage.Field(session=True)
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

