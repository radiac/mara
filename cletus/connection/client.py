"""
Manage connections

Based on miniboa's telnet.py
http://miniboa.googlecode.com/svn/trunk/miniboa/telnet.py
"""

import socket
import select

from .. import events
from .. import util


#
# miniboa's useful notes
#

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
    Simple class used to track the status of a Telnet option
    """
    def __init__(self):
        self.local = UNKNOWN    # Local state of an option
        self.remote = UNKNOWN   # Remote state of an option
        self.pending = False    # Are we expecting a reply?

class Client(object):
    """
    Telnet client socket manager
    """
    
    def __init__(self, service, socket):
        # Store vars
        self.service = service
        self.socket = socket
        
        # Look up settings
        self.settings = service.settings
        self.timeout_time = self.settings.socket_timeout
        
        # Find IP
        (self.ip, port) = self.socket.getpeername()
    
        # Make a note of when the connection started
        self._connect_time = self.service.time
        self._last_activity = self._connect_time
        
        # Connection management
        self._is_connected = True   # Is currently connected
        self._is_closing = False    # Will close once everything is sent
        
        # See if we should wait for a flash policy request
        if self.settings.flash:
            self._flash_waiting = self._connect_time + self.settings.flash_wait
        else:
            self._flash_waiting = None
        
        # Buffers
        self._recv_buffer = ''
        self._send_buffer = ''
            
        # State variables for interpreting incoming telnet commands
        self.got_iac = False    # Are we inside an IAC sequence?
        self.got_cmd = None     # Did we get a telnet command?
        self.got_sb = False     # Are we inside a subnegotiation?
        self.options = {}       # Mapping for up to 256 TelnetOptions
        self.echo = False       # Echo input back to the client?
        self._supress_echo = False   # Override echo option (control with supress_echo)
        self.sb_buffer = ''     # Buffer for sub-negotiations
        self.terminal_type = None
        self.columns = 80
        self.rows = 50
        self.handler = None     # Handler for the next input buffer
        # Start telnet negotiation
        self._tn_request(DO, TTYPE)   # Get terminal type
        self._tn_request(DO, NAWS)    # Do NAWS
        
        # Log
        self.service.log.client('Client %s connected' % self.ip)
        self.service.trigger(events.Connect(self))
    
    is_connected = property(
        fget = lambda self: self._is_connected,
        doc = 'State of the connection'
    )
    is_closing = property(
        fget = lambda self: self._is_closing,
        doc = 'Set if the connection is closing, but still open'
    )
    
    def capture(self, handler):
        """
        The specified handler wants to capture the next input buffer
        """
        self.handler = handler

    def get_idle_age(self):
        """
        Get idle age in human-readable format
        """
        return util.pretty_age(now=self.service.time, then=self._last_activity)
        
    def timeout(self):
        """
        See if the client has timed out
        """
        # Test for no timeout
        if not self.timeout_time:
            return False
            
        if self._last_activity < self.service.time - self.timeout_time:
            self.service.log.client('Client %s timed out' % self.ip)
            return True
            
        return False
    
    def read(self, data):
        """
        Data has arrived
        """
        #print "RECV:%s:%s" % (data, ','.join(["%d" % ord(c) for c in data]))
        
        # If we're closing, not interested
        if self._is_closing:
            return
        
        # Flash check
        if self._flash_waiting:
            self._flash_waiting = None
            if data == '<policy-file-request/>\0':
                return self._flash_policy()
        
        # Update last activity for idle
        self._last_activity = self.service.time
        
        # If not in raw mode, process it
        if not self.settings.socket_raw:
            data = self._process_read(data)
        if data is None:
            # Nothing to process
            return
        
        # Send off for processing
        if self.handler:
            try:
                yielded = self.handler.send(data)
            except StopIteration:
                self.handler = None
        else:
            self.service.trigger(events.Receive(self, data))
    
    @property
    def supress_echo(self):
        """
        Disable echo on client and server.
        
        Use for collecting sensitive information, eg passwords
        """
        return self._supress_echo
    
    @supress_echo.setter
    def supress_echo(self, value):
        self._suppress_echo = value
        if self._suppress_echo:
            self.write_raw(IAC + WILL + ECHO)
        else:
            self.write_raw(IAC + WONT + ECHO)
        
    def _process_read(self, data):
        """
        Process read data when not in raw mode
        """
        # Telnet negotiation
        data = self._negotiate(data)
        if len(data) == 0:
            return
        
        # Echo back to client
        if self.echo and not self._suppress_echo:
            self._send_buffer += data
        
        # Add data to recv_buffer
        self._recv_buffer += data
        if self.settings.internal_buffer_size and len(self._recv_buffer) > self.settings.internal_buffer_size:
            self._recv_buffer = ''
            self.write('Input too long')
        
        # Standardise inbound line endings
        # RFC 854 says \r on its own is not allowed
        self._recv_buffer = self._recv_buffer.replace('\r\n', '\n').replace('\r\0', '\n')
        
        # Test for a complete line
        if not "\n" in self._recv_buffer:
            return None
        
        # Pull off first line
        (line, self._recv_buffer) = self._recv_buffer.split("\n")
        return line
        
    def write(self, *lines):
        """
        Send data with newlines
        """
        # Handle raw mode
        if self.settings.socket_raw:
            return self.write_raw(''.join(lines))
        
        # Resolve special lines
        out = []
        for line in lines:
            if hasattr(line, 'render'):
                line = line.render(self.columns)
            out.append(str(line))
        
        self._send_buffer += "\r\n".join(out) + "\r\n"
        
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
        
    def _test_send_buffer(self):
        # Test for flash waiting expiry
        if self._flash_waiting:
            # If it has not expired, we definitely have nothing to send
            if self.service.time < self._flash_waiting:
                return
            self._flash_waiting = None
        return len(self._send_buffer) > 0
    send_pending = property(
        fget = _test_send_buffer,
        doc = "Check if there's anything on the send buffer"
    )
    
    def _flash_policy(self):
        """
        Send the flash policy
        """
        self.service.log.client('Client %s asked for Flash policy' % self.ip)
        
        # The _flash_waiting flag has been cleared, so overwrite _send_buffer
        self._send_buffer = self.settings.flash_policy % {
            'port': self.settings.port
        } + '\0'
        
        # Close the socket - it will still be able to send, just not read
        self.close()
    
    def flush(self):
        """
        Force the buffer to the socket immediately
        
        Doesn't check that the socket is ready to read, so should only be
        called when you really can't wait for the standard loop
        """
        self.service.server._send_client(self.socket)
    
    def close(self):
        """
        Close gracefully
        """
        if len(self._send_buffer) > 0:
            self._is_closing = True
        else:
            self.shutdown()
            
    def shutdown(self):
        """
        Actually close things
        """
        if self.socket:
            self.socket.close()
        self.disconnected()
    
    def disconnected(self):
        """
        The socket has been closed
        """
        self.service.log.client('Client %s disconnected' % self.ip)
        self.service.trigger(events.Disconnect(client=self))
        self.socket = None
        self._is_connected = False
        self._is_closing = False

    
    #
    # Telnet negotiation
    #
    
    def _negotiate(self, raw):
        """
        Check an input string for telnet commands
        Returns the input string without telnet commands
        """
        # Going to step through the string
        safe = ''
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
                    # Return raw string unchanged
                    safe = raw
                    break
                
                # Have an IAC
                self.got_iac = True
                
                # Pull off anything before the IAC
                safe += raw[0:next_iac]
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
                    safe += cmd
                    continue
                
                # Check for 3-byte command
                elif cmd in [DO, DONT, WILL, WONT]:
                    self.got_cmd = cmd
                
                # Check for sub-negotiation
                elif cmd == SB:
                    self.got_cmd = cmd
                    self.got_sb = True
                
                # Otherwise must be a two-byte command
                else:
                    # ++ DEBUGGING
                    if cmd == NOP:
                        print "IAC NOP"
                    # Just going to ignore these
                    if cmd in [NOP, DATMK, IP, AO, AYT, EC, EL, GA]:
                        pass
                    else:
                        self.service.log.client(
                            'Client %s sent unexpected IAC sequence' % self.ip,
                        )
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
                        self.service.log.client(
                            'Client %s sent invalid IAC SE' % self.ip,
                        )
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
        return safe
        
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
        setting = self.option(option)
        
        #
        # Local status (incoming DO or DONT)
        #
        
        # Either reply: Yes, please do this
        # or request:   I'd like you to do this
        if cmd == DO:
            # Check for recognised option
            if option in [ECHO]:
                # If pending reply, this is the reply
                if setting.pending:
                    setting.pending = False
                    setting.local = True
                    
                # Otherwise request; change if not already True
                elif setting.local is not True:
                    setting.local = True
                    self._tn_reply(WILL, option)
                
                if option == ECHO:
                    self.echo = True
                
            # Otherwise refuse
            else:
                if setting.local is UNKNOWN:
                    setting.local = False
                    self._tn_reply(WONT, option)
        
        # Either reply: No, please don't this
        # or request:   I'd like you to not do this
        elif cmd == DONT:
            if option in [ECHO]:
                if setting.pending:
                    setting.pending = False
                    setting.local = False
                elif setting.local is not False:
                    setting.local = False
                    self._tn_reply(WONT, option)
                    
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
                    self._tn_reply(DONT, ECHO)
            
            elif option in [NAWS, TTYPE]:
                if setting.pending:
                    setting.pending = False
                    setting.remote = True
                    
                    # If TTYPE, ask for TTYPE
                    if option == TTYPE:
                        self.write_raw(IAC+SB+TTYPE+SEND+IAC+SE)
                    
                elif setting.remote is not True:
                    setting.remote = True
                    self._tn_reply(DO, option)
                    
                # If NAWS, client will follow with SB
        
        # Either reply: No, I won't do this
        # or request:   I don't want to do this
        elif cmd == WONT:
            if option == ECHO:
                # A client should not echo the server anyway
                if setting.remote is UNKNOWN:
                    setting.remote = False
                    self._tn_reply(DONT, ECHO)
                
            elif option in [TTYPE]:
                if setting.pending:
                    setting.pending = False
                    setting.remote = False
                
                elif setting.remote is not False:
                    setting.remote = False
                    self._tn_reply(DONT, option)
        
        self.got_iac = False
        self.got_cmd = None
        
    def _sb_decoder(self):
        """
        Figures out what to do with a received sub-negotiation block
        """
        bloc = self.sb_buffer
        if len(bloc) > 2:

            if bloc[0] == TTYPE and bloc[1] == IS:
                self.terminal_type = bloc[2:]

            if bloc[0] == NAWS:
                if len(bloc) != 5:
                    self.service.log.client(
                        'Client %s sent invalid IAC NAWS block' % self.ip
                    )
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
    
    def _tn_reply(self, cmd, option):
        """
        Send a telnet negotiation reply
        """
        self.write_raw(IAC + cmd + option)
    
    def _tn_request(self, cmd, option):
        """
        Send a telnet negotiation request
        """
        self.option(option).pending = True
        self.write_raw(IAC + cmd + option)
    