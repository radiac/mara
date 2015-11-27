"""
Client container
"""

class ClientContainer(object):
    """
    Client container
    
    Holds a list of clients, allows filtering and bulk writes
    
    Containers are not directly managed across restarts; you should consider
    using storage.ClientContainer and storage.SessionClientContainer instead.
    """
    _clients = None
    
    def __init__(self):
        self._clients = []
        
    clients = property(lambda self: self._clients)
    
    def add_client(self, client):
        self._clients.append(client)
        
    def remove_client(self, client):
        self._clients.remove(client.id)
    
    def write(self, clients, *data):
        """
        Send the provided lines to the given client, or list of clients
        """
        if not hasattr(clients, '__iter__'):
            clients = [clients]
        for client in clients:
            client.write(*data)
    
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
