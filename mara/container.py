"""
Client container
"""
from __future__ import unicode_literals

from . import util


class ClientContainer(object):
    """
    Client container
    
    Holds a list of clients, allows filtering and bulk writes
    
    Containers are not directly managed across restarts; you should consider
    using storage.ClientContainer and storage.SessionClientContainer instead.
    """
    _clients = None
    
    def __init__(self, *args, **kwargs):
        """
        Initialise a container
        
        Designed to be mixed into other classes, so takes any arguments and
        ignores them.
        """
        self._clients = []
        super(ClientContainer, self).__init__(*args, **kwargs)
        
    clients = property(lambda self: self._clients)
    
    def add_client(self, client):
        self._clients.append(client)
        
    def remove_client(self, client):
        self._clients.remove(client.id)
    
    def write(self, clients, *data, **kwargs):
        """
        Send the provided lines to the given client, or list of clients
        """
        if not hasattr(clients, '__iter__'):
            clients = [clients]
        for client in clients:
            client.write(*data, **kwargs)
    
    def write_all(self, *data, **kwargs):
        """
        Send the provided lines to all active clients, as returned by
        filter_clients(**kwargs)
        
        Takes the same arguments as filter_clients()
        """
        # Get client list
        clients = self.filter_clients(**kwargs)
        
        # Write data to the clients
        for client in clients:
            client.write(*data)
    
    def filter_clients(self, filter_fn=None, exclude=None):
        """
        Get a list of clients, filtered by the global filter, a local filter
        and an exclude list
        """
        # Capture kwargs
        if exclude is None:
            exclude = []
        elif not hasattr(exclude, '__iter__'):
            exclude = [exclude]
            
        # Filter the client list using exclude list
        clients = [client for client in self.clients if client not in exclude]
        
        # Further filtering for this call
        if filter_fn:
            clients = filter_fn(self, clients)
        
        return clients
    
    msg_who = '%(others)s %(are)s %(where)s.'
    def get_who(self, exclude=None, where='here'):
        """
        Return a string of users who are in the container
        
        If client.user.name is available (ie contrib.user is being used) the
        names of the clients will be shown; otherwise it will be the number of
        clients (eg "5 are here")
        
        Fills out the string msg_who; the ``where`` argument can be overridden
        to change it from 'here', eg 'there', 'online' etc.
        """
        # Find others here
        other_clients = self.filter_clients(exclude=exclude)
        try:
            others = [client.user.name for client in other_clients]
        except AttributeError:
            others = ['%d' % len(other_clients)]
        else:
            if not others:
                if exclude:
                    others = ['Nobody else']
                else:
                    others = ['Nobody']
        
        # Welcome user
        return self.msg_who % {
            'others':   util.pretty_list(sorted(others)),
            'are':      'is' if len(others) == 1 else 'are',
            'where':    where,
        }
