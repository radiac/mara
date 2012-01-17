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
                if user.is_connected and user.send_pending:
                    send_pending.append(client_socket)
            
            
            #
            # Check sockets
            #
            
            # Check all sockets for reads (server sockets)
            read_sockets = []
            send_sockets = []
            try:
                # Use select without a timeout, to block until there's something to read
                read_sockets, send_sockets = select.select(
                    [self.serversocket.socket] + self._client_sockets,
                    send_pending, [], self.settings.listen_for
                )[0:2]
            except select.error, e:
                log.server('Server select error: %s' % e)
            except socket.error, e:
                log.server('Server socket error: %s' % e)
            
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


#
# Telnet negotiation constants
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

class TelnetOption(object):
    """
    Simple class used to track the status of an extended Telnet option
    """
    def __init__(self):
        self.local = UNKNOWN    # Local state of an option
        self.remote = UNKNOWN   # Remote state of an option
        self.pending = False    # Are we expecting a reply?

class TelnetState(object):
    """
    Telnet negotiation
    Based on miniboa
    http://miniboa.googlecode.com/svn/trunk/miniboa/telnet.py
    """
    
    """
    See RFC 854 for more information
    
    Negotiating a Local Option
    --------------------------
    Side A sends:
        "IAC WILL/WONT XX"   Meaning "I would like to [use|not use] option XX."
    Side B replies:
        "IAC DO XX"     "OK, you may use option XX."
        "IAC DONT XX"   "No, you cannot use option XX."

    Negotiating a Remote Option
    ----------------------------
    Side A sends:
        "IAC DO/DONT XX"  Meaning "I would like YOU to [use|not use] option XX."
    Side B replies:
        "IAC WILL XX"   Meaning "I will begin using option XX"
        "IAC WONT XX"   Meaning "I will not begin using option XX"
        
    The syntax is designed so that if both parties receive simultaneous requests
    for the same option, each will see the other's request as a positive
    acknowledgement of it's own.
    
    If a party receives a request to enter a mode that it is already in, the
    request should not be acknowledged.

    Where you see DE in my comments I mean 'Distant End', e.g. the client.
    """
    

    def __init__(self, user):
        self.user = user
        
        # State variables for interpreting incoming telnet commands
        self.got_iac = False    # Are we inside an IAC sequence?
        self.got_cmd = None     # Did we get a telnet command?
        self.got_sb = False     # Are we inside a subnegotiation?
        self.options = {}       # Mapping for up to 256 TelnetOptions
        self.echo = False       # Echo input back to the client?
        self.echo_password = False  # Echo back '*' for passwords?
        self.sb_buffer = ''     # Buffer for sub-negotiations
    
    def process(self, raw):
        """
        Check an input string for telnet commands
        Returns the input string without telnet commands
        """
        # Going to step through the string
        while True:
            #
            # First byte: IAC
            #
            
            # Make sure we're in an IAC
            if not self.got_iac:
                # Look for next IAC
                next_iac = raw.find(IAC)
                
                # Catch no IAC
                if next_iac == -1:
                    break
                
                # Have an IAC
                self.got_iac = True
                
                # Pull off anything before the IAC
                if next_iac > 0:
                    self.user._recv_buffer += raw[0:next_iac]
                    raw = raw[next_iac + 1:]
            
            # We're in an IAC
            # Check there's something left to read
            if len(raw) == 0:
                break
            
            
            #
            # Second byte: CMD
            #
            
            # Make sure we have a command
            if not self.got_cmd:
                # The next byte follows the IAC, so will be interesting
                cmd = raw[0]
                raw = raw[1:]
                
                # Check for escaped IAC
                if cmd == IAC:
                    self.got_iac = False
                    self.user._recv_buffer += cmd
                    continue
                
                # Check for 3-byte command
                elif cmd in [DO, DONT, WILL, WONT]:
                    self.got_cmd = cmd
                
                # Check for sub-negotiation
                elif cmd == SE:
                    self.got_cmd = cmd
                    self.got_sb = True
                
                # Otherwise must be a two-byte command
                else:
                    # Just going to ignore these
                    if cmd in [NOP, DATMK, IP, AO, AYT, EC, EL, GA]:
                        pass
                    else:
                        log.client('Client sent unexpected char after IAC')
                    self.got_iac = False
                    continue
            
            # We're in an IAC CMD
            # Check there's something left to read
            if len(raw) == 0:
                break
            
            
            #
            # Third byte: 3 byte command or subnegotiation
            #
            
            # Check for sub-negotiation
            if self.got_sb:
                # Look for end, checking that IAC are not escaped
                while True:
                    next_esc_iac = raw.find(IAC + IAC)
                    next_se = raw.find(IAC + SE)
                    if next_esc_iac > -1 and next_esc_iac < next_se:
                        self.sb_buffer += raw[0:next_esc_iac + 2]
                        raw = raw[next_esc_iac + 2:]
                        # Try again
                    else:
                        # Either no IAC IAC before IAC SE, or no IAC SE
                        break
                
                # Check for IAC SE
                if next_se == -1:
                    self.sb_buffer += raw
                    raw = ''
                    
                    # Sanity check
                    if len(self.sb_buffer) > 64:
                        log.client('Client sent IAC SE which was too long')
                        # Put rest of buffer back on
                        raw = self.sb_buffer[65:]
                        self._sb_done()
                    
                # Otherwise found the end
                else:
                    self.sb_buffer += raw[0:next_se]
                    raw = raw[next_se + 2:]
                    self._sb_decoder()
                    self._sb_done()
            
            # Otherwise it must be a 3 byte command
            else:
                option = raw[0]
                raw = raw[1:]
                self._three_byte_cmd(option)
            
            # Continue processing the rest of the string
            
        # The raw string is either clear or empty
        return raw
        
    def option(self, option):
        """
        Get an option object
        """
        if not self.options.has_key(option):
            self.options[option] = TelnetOption()
        return self.options[option]
    
    def _three_byte_cmd(self, option):
        """
        Handle incoming Telnet commmands that are three bytes long
        """
        # Get command and setting for this option
        cmd = self.got_cmd
        setting = self.options(option)
        
        
        #
        # Local status (incoming DO or DONT)
        #
        
        # Either reply: Yes, please do this
        # or request:   I'd like you to do this
        if cmd == DO:
            # Check for recognised option
            if option in [BINARY, ECHO, SGA]:
                # If pending reply, this is the reply
                if setting.pending:
                    setting.pending = False
                    setting.local = True
                    
                # Otherwise request; change if not already True
                elif setting.local is not True:
                    setting.local = True
                    self._iac_will(option)
                
                if option == ECHO:
                    self.echo = True
                
            # Otherwise refuse
            else:
                if setting.local is UNKNOWN:
                    setting.local = False
                    self._iac_wont(option)
        
        # Either reply: No, please don't this
        # or request:   I'd like you to not do this
        elif cmd == DONT:
            if option in [BINARY, ECHO, SGA]:
                if setting.pending:
                    setting.pending = False
                    setting.local = False
                elif setting.local is not False:
                    setting.local = False
                    self._iac_wont(option)
                    # ++ miniboa sends iac_will(SGA)?
                    
                if option == ECHO:
                    self.echo = False
                    
            else:
                # Just ignore, weren't going to do it anyway
                pass
        
        #
        # Remote end (incoming WILL or WONT)
        #
        
        # Either reply: Sure, I'll do this
        # or request:   I'd like to do this
        elif cmd == WILL:
            if option == ECHO:
                # A client should not echo the server
                if setting.remote is UNKNOWN:
                    setting.remote = False
                    self._iac_dont(ECHO)
            
            elif option == NAWS:
                if setting.pending:
                    setting.pending = False
                    setting.remote = True
                    # Client will follow with SB
                    
                elif setting.remote is not True:
                    setting.remote = True
                    self._iac_do(option)
                    # Client will follow with SB
                    
        # Incoming WILL and WONT refer to the status of the other end (remote)
        # 
        
        
    def _sb_decoder(self):
        """
        Figures out what to do with a received sub-negotiation block
        """
        #print "at decoder"
        bloc = self.sb_buffer
        if len(bloc) > 2:

            if bloc[0] == TTYPE and bloc[1] == IS:
                self.terminal_type = bloc[2:]
                #print "Terminal type = '%s'" % self.terminal_type

            if bloc[0] == NAWS:
                if len(bloc) != 5:
                    log.client('Client sent invalid IAC NAWS block')
                else:
                    self.columns = (256 * ord(bloc[1])) + ord(bloc[2])
                    self.rows = (256 * ord(bloc[3])) + ord(bloc[4])

    def _sb_done(self):
        """
        The sub-negotiation is finished
        """
        self.got_iac = False
        self.got_cmd = False
        self.got_sb = False
        self.sb_buffer = ''
        