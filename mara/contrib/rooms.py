"""
Mara rooms
"""
from ... import container
from ... import storage 


class Room(container.ClientContainer, storage.Store):
    users = storage.Field(lambda: [])

    def find_user(self, name):
        """
        Find a User in this room from a name
        """
        if not name:
            return None
        
        for user in self.users:
            if user.name == name:
                return user
        return None

    def find_others(self, target):
        """
        Get a list of users in this room, excluding the specified user
        """
        return [user for user in self.users if user != target]
    
    def write_all(self, *lines, **kwargs):
        """
        Write something to everyone in the room
        """
        filter_fn = kwargs.get('filter', lambda s, cs: cs)
        filter_fn = lambda s, cs: [
            c for c in filter_fn(s, cs) if c.user.room == self
        ]
        kwargs['filter'] = filter_fn
        self.service.write_all(*lines, **kwargs)
        
    def list_users(self, user):
        """
        Tell the specified user who else is here
        """
        others = self.find_others(user)
        if len(others) >= 1:
            user.write('Also here: %s' % ', '.join([o.name for o in others]))
        else:
            user.write('Nobody else is here.')
