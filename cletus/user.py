"""
User management
"""

import datetime

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
        self.buffer = ''
        self._prompt = None
        
        # User data
        self._data = {
            'core': {
                'name': None
            }
        }
        
    is_connected = property(
        fget = lambda self: self._is_connected,
        doc = 'State of the connection'
    )
    
    # Name is common to all managers and plugins; make easy to access
    name = property(
        fget = lambda self: self._data['core']['name'],
        fset = lambda self, name: self._data['core'].__setitem__('name', name),
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
        
        # Add data to buffer
        self.buffer += data
        
        # Test for buffer limit
        if self.settings.internal_buffer_size and len(self.buffer) > self.settings.internal_buffer_size:
            self.buffer = ''
            self.write('Input too long')
        
        # Test for a complete line
        if not "\r\n" in self.buffer:
            return
        
        # Split off first line
        (line, self.buffer) = self.buffer.split("\r\n")
        
        # See if this is a prompt
        if self._prompt:
            if self._prompt.has_key('validate'):
                if not self._prompt['validate'](self, line):
                    self.prompt(**self._prompt)
                    return
            
            # Get the callback, then clear the prompt        
            callback = self._prompt['callback']
            self._prompt = None
            callback(self, line)
            
        else:
            self.manager.process(self, line)
        
    def write(self, *lines):
        """
        Send data
        """
        self.socket.send("\r\n".join(lines) + "\r\n")
    
    def prompt(self, prompt, callback, validate=None):
        """
        Send a prompt and get a single line in response
        The callback and validate functions will be passed:
            user    This user
            data    The response from the user
        The validate function must return a boolean value
        """
        self.socket.send(prompt)
        self._prompt = {
            'prompt':   prompt,
            'callback': callback,
            'validate': validate
        }
        
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
        self._is_connected = False
