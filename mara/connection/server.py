"""
Manage connections
"""
from __future__ import unicode_literals

import socket
import select

from .client import Client
from .util import serialise_socket, deserialise_socket
from .. import events


class ServerSocket(object):
    """
    Manage a non-blocking server socket to accept connections
    """
    def __init__(self, settings, serialised=None):
        """
        Initialise and call open()
        """
        self.settings = settings
        self.socket = None
        if serialised:
            self.deserialise(serialised)
    
    def serialise(self):
        return serialise_socket(self.socket)
    
    def deserialise(self, data):
        self.socket = deserialise_socket(data)
    
    def open(self):
        # Called from listen, so make sure it's safe to run when already open
        # This can happen when we've deserialised an open socket
        if self.socket:
            return
        
        # Create and bind
        self.socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM
        )
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.settings.host, int(self.settings.port)))
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
            
        return client_socket
        
    def close(self):
        """
        Close gracefully
        """
        if self.socket:
            self.socket.close()
        self.socket = None


class Server(object):
    """
    Manage the Socket and connections
    Arguments:
        service     A Service instance
    """
    # Not running (exit the main loop)
    _running = False
    
    def __init__(self, service, serialised=None):
        # Store data
        self.service = service
        self.settings = service.settings
        
        # List of all client sockets
        self._client_sockets = []
        
        # Dict of all Client objects (socket->client)
        self._clients = {}
        
        # Create the server socket, or restore a serialised one
        if serialised:
            self.deserialise(serialised)
        else:
            self.serversocket = ServerSocket(self.settings)
        
    running = property(
        fget = lambda self: self._running,
        doc = 'Whether or not the server is running'
    )
    
    def serialise(self):
        """
        Serialise to be passed to a new process
        """
        clients = []
        for client in self._clients.values():
            serialised = client.serialise()
            if not serialised:
                # Serialisation failed, skip
                continue
            clients.append(serialised)
        
        return {
            'clients': clients,
            'serversocket': self.serversocket.serialise(),
        }
    
    def deserialise(self, data):
        """
        Deserialise a serialised Server into this instance
        """
        self.serversocket = ServerSocket(
            self.settings, serialised=data['serversocket'],
        )
        
        for client_data in data['clients']:
            client = Client(self.service, socket=None, serialised=client_data)
            self._client_sockets.append(client.socket)
            self._clients[client.socket] = client
    
    def listen(self):
        """
        Loop while listening for connections and incoming data
        """
        self.serversocket.open()
        self.service.log.server('Server listening on %s:%s' % (
            self.settings.host, self.settings.port
        ))
        self.service.trigger(events.server.ListenStart(
            host=self.settings.host,
            port=self.settings.port,
        ))
        
        self._running = True
        while self._running:
            #
            # Check all clients
            #
            send_pending = []
            
            # Loop backwards so we can delete as we go
            for i in xrange(len(self._client_sockets)-1, -1, -1):
                client_socket = self._client_sockets[i]
                client = self._clients[client_socket]
                
                # Timeouts
                if client.timeout():
                    client.write('You have been idle for too long')
                    client.close()
                
                # Disconnected
                if not client.is_connected:
                    del self._clients[client_socket]
                    del self._client_sockets[i]
                    
                # Client has data on the send buffer
                if client.is_connected and client.send_pending:
                    send_pending.append(client_socket)
            
            
            #
            # Check sockets
            #
            
            # Check all sockets for reads (server sockets)
            read_sockets = []
            send_sockets = []
            try:
                # Use select without a timeout, to block until there's
                # something to read
                read_sockets, send_sockets = select.select(
                    [self.serversocket.socket] + self._client_sockets,
                    send_pending, [], self.settings.socket_activity_timeout
                )[0:2]
            except select.error as e:
                self.service.log.server('Server select error: %s' % e)
            except socket.error as e:
                self.service.log.server('Server socket error: %s' % e)
            
            # Poll the service now to update time and run overdue game ticks
            self.service.poll()
            
            # Process all sockets with something to read
            for read_socket in read_sockets:
                # New connection
                if read_socket == self.serversocket.socket:
                    self._new_client(read_socket)
                    
                # Incoming from client
                elif read_socket in self._client_sockets:
                    # Read from the client and find session
                    self._read_client(read_socket)
                
            # Process all sockets ready to send
            for send_socket in send_sockets:
                self._send_client(send_socket)
        
        self.service.log.server('Server stopped listening')
        self.service.trigger(events.server.ListenStop())
    
    def _new_client(self, read_socket):
        """
        A new client has connected; accept and register
        """
        client_socket = self.serversocket.accept()
        
        if not client_socket:
            return
        
        # Add to known client sockets
        self._client_sockets.append(client_socket)
        
        # Create new client and register
        client = Client(self.service, client_socket)
        self._clients[client_socket] = client
        
    def _read_client(self, read_socket):
        """
        A client has sent data
        """
        # Find client
        client = self._clients[read_socket]
        
        # Read data
        try:
            data = read_socket.recv(self.settings.socket_buffer_size)
        except socket.error:
            # We were told there was something to read, but there is not
            # Mark as disconnected, to be cleaned up next loop
            client.disconnected()
            return
        
        # Send it on to the client object
        if len(data) > 0:
            client.read(data)
    
    def _send_client(self, send_socket):
        """
        A client is ready to receive data
        """
        # Find client
        client = self._clients[send_socket]
        
        # Send data
        data = client.send_buffer
        try:
            sent = send_socket.send(data)
        except socket.error:
            # We were told the socket was ready to send, but it is not
            # Mark as disconnected, to be cleaned up next loop
            client.disconnected()
            return
        
        # See if there is something left to send
        if sent < len(data):
            client.write_raw(data[sent:])
        
        # See if it should close now
        elif client.is_closing:
            client.shutdown()
        
    def suspend(self):
        """
        Stops the main loop, while maintaining connections
        Restart by calling Server.listen()
        """
        self.service.log.server('Server suspending')
        self.service.trigger(events.server.Suspend())
        self._running = False
    
    def shutdown(self):
        """
        Close all open connections and prepare to die
        """
        # Start logging
        self.service.log.server('Server shutting down')
        
        # Close all client sockets
        for client_socket in self._client_sockets:
            client_socket.close()
        self._client_sockets = []
        self._clients = {}
        
        # Close the server socket
        if self.serversocket:
            self.serversocket.close()
        
        # Not running (exit the main loop)
        self._running = False
    
    def __del__(self):
        self.service.log.server('Server stopped')
