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
        self.settings = manager.settings;
        
        # Make a note of when the connection started
        self._connected_at = datetime.datetime.now()
        self._last_activity = self._connected_at
        
        # Connection management
        self._is_connected = True
        self.buffer = ''
        self._prompt = None
        
        # Additional settings
        self.name = None
        
    is_connected = property(
        fget = lambda self: self._is_connected,
        doc = 'State of the connection'
    )
    
    def timeout(self, now):
        """
        Try to time out the user
        """
        limit = now
        
        if self.name:
            limit -= self.settings.timeout_connected
        else:
            limit -= self.settings.timeout_user
            
        age = self._last_activity + self.settings.timeout_connected
        if self._last_activity
    
    def read(self, data):
        """
        Data has arrived
        """
        self.buffer += data
        
        # Test for a complete line
        if not "\r\n" in self.buffer:
            return
        
        # Split off first line
        (line, self.buffer) = self.buffer.split("\r\n")
        
        # See if this is a prompt
        if self._prompt:
            if self._prompt.has_key('validate'):
                if not self._prompt['validate'](self, line)
                    self.prompt(**self._prompt)
                    return
            self._prompt['callback'](self, line)
            
        else:
            self.manager.process(self, line)
        
    def write(self, data):
        """
        Send data
        """
        self.socket.send(data + "\r\n")
    
    def prompt(self, prompt, callback, validate=None):
        """
        Send a prompt and get a single line in response
        The callback and validate functions will be passed:
            user    This user
            data    The response from the user
        The validate function must return a boolean value
        """
        self.socket.send(data)
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
