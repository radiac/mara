"""
User management
"""

import datetime
import socket

class User(object):
    """
    Manage a client
    """
    def __init__(self, manager, client_socket):
        # Store vars
        self.manager = manager;
        self.socket = client_socket;
        
        # Cache things
        self.settings = manager.settings;
        (self.ip, port) = self.socket.getpeername()
        
        # Make a note of when the connection started
        self._connected_at = datetime.datetime.now()
        self._last_activity = self._connected_at
        
        # Connection management
        self._is_connected = True
        self._recv_buffer = ''
        self._send_buffer = ''
        self._prompt = None
        
        # User data which can be saved
        # Profile info, location data etc
        self._store = {
            'profile': {
                'name': None
            }
        }
        
        # User data which can't be saved
        # Game info etc
        self._session = {}
        
    is_connected = property(
        fget = lambda self: self._is_connected,
        doc = 'State of the connection'
    )
    
    def store(self, name):
        """
        Get a store dict
        """
        if not self._store.has_key(name):
            self._store[name] = {}
        return self._store[name]
    
    def session(self, name):
        """
        Get a session dict
        """
        if not self._session.has_key(name):
            self._session[name] = {}
        return self._session[name]
        
    # Name is going to be common to almost all use-cases - make it easy to access
    name = property(
        fget = lambda self: self.store('profile')['name'],
        fset = lambda self, name: self.store('profile').__setitem__('name', name),
        doc = 'Get or set the user name'
    )
    
    def timeout(self, when):
        """
        See if the user has timed out at the given time
        """
        if self.name:
            # Test for no timeout
            if not self.settings.timeout_named:
                return False
            when -= self.settings.timeout_named
            
        else:
            # Not named
            when -= self.settings.timeout_unnamed
            
        if self._last_activity < when:
            return True
            
        return False
    
    def read(self, data):
        """
        Data has arrived
        """
        # Update last activity for idle
        self._last_activity = datetime.datetime.now()
        
        # Add data to recv_buffer
        self._recv_buffer += data
        
        # Test for buffer limit
        if self.settings.internal_buffer_size and len(self._recv_buffer) > self.settings.internal_buffer_size:
            self._recv_buffer = ''
            self.write('Input too long')
        
        # Test for a complete line
        if not "\r\n" in self._recv_buffer:
            return
        
        # Send first line for processing
        (line, self._recv_buffer) = self._recv_buffer.split("\r\n")
        self.manager.input(self, line)
        
    def write(self, *lines):
        """
        Send data with newlines
        """
        self._send_buffer += "\r\n".join(lines) + "\r\n"
        
    def write_raw(self, raw):
        self._send_buffer += raw
    
    def _get_send_buffer(self):
        out = self._send_buffer
        self._send_buffer = ''
        return out
    send_buffer = property(
        fget = _get_send_buffer,
        doc="Get the send buffer and empty it"
    )
    send_pending = property(
        fget = lambda self: len(self._send_buffer) > 0,
        doc = "Check if there's anything on the send buffer"
    )
    
    def close(self):
        """
        Close gracefully
        """
        if self.socket:
            self.socket.close()
        self.disconnected()
    
    def disconnected(self):
        """
        The socket has been closed
        """
        self.socket = None
        self._is_connected = False
