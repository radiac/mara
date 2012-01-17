"""
Manage connections
"""
import datetime
import socket
import select

import cletus.log as log
from cletus.user import User
    
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
        log.server('Server started')
        
        # Store data
        self.manager = manager
        self.settings = self.manager.settings
        
        # List of all client sockets
        self._client_sockets = []
        
        # Dict of all User objects (socket->user)
        self._users = {}
        
        # Create a the server socket
        self.serversocket = ServerSocket(self.settings)
        
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
        log.server('Server listening')
        
        self._running = True
        while self._running:
            #
            # Check all users
            #
            now = datetime.datetime.now()
            send_pending = []
            
            # Loop backwards so we can delete as we go
            for i in xrange(len(self._client_sockets)-1, -1, -1):
                client_socket = self._client_sockets[i]
                user = self._users[client_socket]
                
                # Timeouts
                if user.timeout(now):
                    log.client('Client %s timed out' % client_socket)
                    user.write('You have been idle for too long')
                    user.close()
                
                # Disconnected
                if not user.is_connected:
                    self.manager.remove_user(user)
                    del self._users[client_socket]
                    del self._client_sockets[i]
                
                # User has data on the send buffer
                if user.send_pending:
                    send_pending.append(client_socket)
            
            
            #
            # Check sockets
            #
            
            # Check all sockets for reads (server sockets)
            read_sockets = None
            send_sockets = None
            try:
                # Use select without a timeout, to block until there's something to read
                read_sockets, send_sockets = select.select(
                    [self.serversocket.socket] + self._client_sockets,
                    send_pending, [], self.settings.listen_for
                )[0:2]
            except select.error, e:
                pass
            except socket.error, e:
                pass
            
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
            
            # Poll the manager
            self.manager.poll()
            
        log.server('Server stopped listening')
                        
    def _new_client(self, read_socket):
        """
        A new client has connected; accept and register
        """
        client_socket = self.serversocket.accept()
        
        if client_socket:
            # Add to known client sockets
            self._client_sockets.append(client_socket)
            log.client('Client %s connected' % client_socket)
            
            # Create new client and register
            user = User(self.manager, client_socket)
            self.manager.add_user(user)
            self._users[client_socket] = user
    
    def _read_client(self, read_socket):
        """
        A user has sent data
        """
        # Find user
        user = self._users[read_socket]
        
        # Read data
        try:
            data = read_socket.recv(self.settings.socket_buffer_size)
        except socket.error, e:
            # Socket has errored; mark as disconnected, to be cleaned up next loop
            log.client('Client %s disconnected' % read_socket)
            user.disconnected()
            return
            
        # Send it on to the user object
        user.read(data)
    
    def _send_client(self, send_socket):
        """
        A user is ready to receive data
        """
        # Find user
        user = self._users[send_socket]
        
        # Send data
        try:
            send_socket.send(user.send_buffer)
        except socket.error, e:
            user.disconnected()
        
    def suspend(self):
        """
        Stops the main loop, while maintaining connections
        Restart by calling Server.listen()
        """
        log.server('Server suspending')
        self._running = False
    
    def shutdown(self):
        """
        Close all open connections and prepare to die
        """
        # Start logging
        log.server('Server shutting down')
        
        # Close all client sockets
        for client_socket in self.client_sockets:
            client_socket.close()
        self.client_sockets = []
        
        # Close the server socket
        if self.serversocket:
            self.serversocket.close()
        
        # Not running (exit the main loop)
        self._running = False
    
    def __del__(self):
        log.server('Server stopped')
    
"""
IAC = '\xff'
REQ = {'WILL':'\xfb','DO':'\xfc','WONT':'\xfd','DONT':'\xfe'}
OPTION = {'ECHO':'\x01' , 'AHEAD':'\x03' }

def getIACCommand(req,option):
    buf = IAC + REQ[req] + OPTION[option]
    return buf
"""

class TelnetNegotiatorServer(object):
    """
    Server-side telnet negotiation
    """
    
    """
    Based heavily on miniboa
    http://miniboa.googlecode.com/svn/trunk/miniboa/telnet.py
    See RFC 854 for more information
    
    Negotiating a Local Option
    --------------------------
    Side A begins with:
        "IAC WILL/WONT XX"   Meaning "I would like to [use|not use] option XX."
    Side B replies with either:
        "IAC DO XX"     "OK, you may use option XX."
        "IAC DONT XX"   "No, you cannot use option XX."

    Negotiating a Remote Option
    ----------------------------
    Side A begins with:
        "IAC DO/DONT XX"  Meaning "I would like YOU to [use|not use] option XX."
    Side B replies with either:
        "IAC WILL XX"   Meaning "I will begin using option XX"
        "IAC WONT XX"   Meaning "I will not begin using option XX"
        
    The syntax is designed so that if both parties receive simultaneous requests
    for the same option, each will see the other's request as a positive
    acknowledgement of it's own.
    
    If a party receives a request to enter a mode that it is already in, the
    request should not be acknowledged.

    Where you see DE in my comments I mean 'Distant End', e.g. the client.
    """
    
    #
    # Constants
    #
    
    UNKNOWN = -1
    
    # Telnet commands
    SE      = chr(240)      # End of subnegotiation parameters
    NOP     = chr(241)      # No operation
    DATMK   = chr(242)      # Data stream portion of a sync.
    BREAK   = chr(243)      # NVT Character BRK
    IP      = chr(244)      # Interrupt Process
    AO      = chr(245)      # Abort Output
    AYT     = chr(246)      # Are you there
    EC      = chr(247)      # Erase Character
    EL      = chr(248)      # Erase Line
    GA      = chr(249)      # The Go Ahead Signal
    SB      = chr(250)      # Sub-option to follow
    WILL    = chr(251)      # Will; request or confirm option begin
    WONT    = chr(252)      # Wont; deny option request
    DO      = chr(253)      # Do = Request or confirm remote option
    DONT    = chr(254)      # Don't = Demand or confirm option halt
    IAC     = chr(255)      # Interpret as Command
    SEND    = chr(001)      # Sub-process negotiation SEND command
    IS      = chr(000)      # Sub-process negotiation IS command

    # Telnet Options
    BINARY  = chr(  0)      # Transmit Binary
    ECHO    = chr(  1)      # Echo characters back to sender
    RECON   = chr(  2)      # Reconnection
    SGA     = chr(  3)      # Suppress Go-Ahead
    TTYPE   = chr( 24)      # Terminal Type
    NAWS    = chr( 31)      # Negotiate About Window Size
    LINEMO  = chr( 34)      # Line Mode
    
    def __init__(self):
        ## State variables for interpreting incoming telnet commands
        self.got_iac = False    # Are we inside an IAC sequence?
        self.got_cmd = None     # Did we get a telnet command?
        self.got_sb = False     # Are we inside a subnegotiation?
        self.opt_dict = {}      # Mapping for up to 256 TelnetOptions
        self.echo = False       # Echo input back to the client?
        self.echo_password = False  # Echo back '*' for passwords?
        self.sb_buffer = ''     # Buffer for sub-negotiations
    
    def process(self, input):
        for byte in input:
            self._iac_sniffer(byte)
            