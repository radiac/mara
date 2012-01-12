"""
Manage connections
"""
import datetime
import socket
import select

from cletus.user import User
import cletus.log as log
    
class ServerSocket(object):
    """
    Manage a non-blocking server socket to accept connections
    """
    def __init__(self, settings):
        """
        Initialise and call open()
        """
        self.settings = settings
        
        self.socket = None
        self.open()
        
    def open(self):
        # Create and bind
        self.socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM
        )
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.settings.host, self.settings.port))
        self.socket.setblocking(0)
        self.socket.listen(5)
    
    def accept(self):
        """
        Check for new connections
        """
        # Look for a connection
        try:
            client_socket, address = self.socket.accept()
        except socket.error:
            # No connection
            return None
        
        # Turn on keepalive
        if self.settings.keepalive:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        
        # Ensure the socket is non-blocking
        client_socket.setblocking(0)
        
        # Create new socket
        return client_socket
        
    def close(self):
        """
        Close gracefully
        """
        if self.socket:
            self.socket.close()


class Server(object):
    """
    Manage the Socket and connections
    Arguments:
        manager     A cletus.core.Manager instance
    """
    def __init__(self, manager):
        log.process('Server started')
        
        # Store data
        self.manager = manager
        self.settings = self.manager.settings
        
        # Register with the manager
        self.manager.set_server(self)
        
        # List of all client sockets
        self._client_sockets = []
        
        # Dict of all User objects (socket->user)
        self._users = {}
        
        # Create a the server socket
        self.socket = ServerSocket(self.settings)
        
        # Not running (exit the main loop)
        self._running = False
        
    running = property(
        fget = lambda self: self._running,
        doc = 'Whether or not the server is running'
    )
    
    def listen(self):
        """
        Loop while listening for connections and incoming data
        """
        log.process('Server listening')
        
        self._running = True
        while self._running:
            #
            # Clean up dead connections
            #
            now = datetime.datetime.now()
            
            # Loop backwards so we can delete as we go
            for i in xrange(len(self._clients_sockets)-1, -1, -1):
                socket = self._client_sockets[i]
                user = self._users[socket]
                
                # Timeouts
                if user.timeout(now):
                    user.close()
                
                # Disconnected
                if not user.is_connected:
                    self.manager.remove_user(user)
                    del self._users[socket]
                    del self._client_sockets[i]
            
            
            #
            # Read sockets
            #
            
            # Check all sockets for reads (new connection, incoming from client, outgoing from server)
            read_sockets = None
            try:
                # Use select without a timeout, to block until there's something to read
                read_sockets = select.select([self.socket.socket] + self._client_sockets, [], [])[0]
            except select.error, e:
                pass
            except socket.error, e:
                pass
            
            # Process all sockets with something to read
            for read_socket in read_sockets:
                # New connection
                if read_socket == self.server.socket:
                    self._new_client(read_socket)
                    
                # Incoming from client
                elif read_socket in self._client_sockets:
                    # Read from the client and find session
                    self._read_client(read_socket)
            
        log.process('Server stopped listening')
                        
    def _new_client(self, read_socket):
        """
        A new client has connected; accept and register
        """
        client_socket = self.server.accept()
        
        # Test for capacity
        if settings.max_connections and len(self._client_sockets) >= settings.max_connections:
            client_socket.send('The server is at capacity - please try again later.')
            client_socket.close()
            return
        
        if client_socket:
            # Add to known client sockets
            self._client_sockets.append(client_socket)
            
            # Create new client and register
            user = User(self.manager, client_socket)
            self.manager.add_user(user)
            self._users[client_socket] = user
    
    def _read_client(self, read_socket):
        """
        A user has sent data
        """
        user = self._clients[read_socket]
        
        # Read data
        try:
            data = client_socket.recv(self.settings.buffer_size)
        except socket.error, e:
            # Socket has errored; mark as disconnected, to be cleaned up next loop
            user.disconnected()
            return
            
        user.read(data)
    
    def suspend(self):
        """
        Stops the main loop, while maintaining connections
        Restart by calling Server.listen()
        """
        log.process('Server suspending')
        self._running = False
    
    def shutdown(self):
        """
        Close all open connections and prepare to die
        """
        # Start logging
        log.process('Server shutting down')
        
        # Close all client sockets
        for client_socket in self.client_sockets:
            client_socket.close()
        self.client_sockets = []
        
        # Close the server socket
        if self.socket:
            self.socket.close()
        
        # Not running (exit the main loop)
        self._running = False
    
    def __del__(self):
        log.process('Server stopped')
    