"""
Telnet protocol
"""

#
# Telnet negotiation: miniboa's useful notes
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
import six

from .
.util import Buffer
from .base import Protocol


#
# Telnet negotiation constants
#

UNKNOWN = -1

# Telnet commands
SE      = six.int2byte(240)     # End of subnegotiation parameters
NOP     = six.int2byte(241)     # No operation
DATMK   = six.int2byte(242)     # Data stream portion of a sync.
BREAK   = six.int2byte(243)     # NVT Character BRK
IP      = six.int2byte(244)     # Interrupt Process
AO      = six.int2byte(245)     # Abort Output
AYT     = six.int2byte(246)     # Are you there
EC      = six.int2byte(247)     # Erase Character
EL      = six.int2byte(248)     # Erase Line
GA      = six.int2byte(249)     # The Go Ahead Signal
SB      = six.int2byte(250)     # Sub-option to follow
WILL    = six.int2byte(251)     # Will; request or confirm option begin
WONT    = six.int2byte(252)     # Wont; deny option request
DO      = six.int2byte(253)     # Do = Request or confirm remote option
DONT    = six.int2byte(254)     # Don't = Demand or confirm option halt
IAC     = six.int2byte(255)     # Interpret as Command
SEND    = six.int2byte(  1)     # Sub-process negotiation SEND command
IS      = six.int2byte(  0)     # Sub-process negotiation IS command

# Telnet Options
BINARY  = six.int2byte(  0)     # Transmit Binary
ECHO    = six.int2byte(  1)     # Echo characters back to sender
RECON   = six.int2byte(  2)     # Reconnection
SGA     = six.int2byte(  3)     # Suppress Go-Ahead
TTYPE   = six.int2byte( 24)     # Terminal Type
NAWS    = six.int2byte( 31)     # Negotiate About Window Size
LINEMO  = six.int2byte( 34)     # Line Mode


class TelnetOption(object):
    """
    Simple class used to track the status of a Telnet option
    """
    def __init__(self, serialised=None):
        self.local = UNKNOWN    # Local state of an option
        self.remote = UNKNOWN   # Remote state of an option
        self.pending = False    # Are we expecting a reply?
        if serialised:
            self.deserialise(serialised)

    def serialise(self):
        return (self.local, self.remote, self.pending)

    def deserialise(self, data):
        self.local, self.remote, self.pending = data


class ProtocolTelnet(Protocol):
    options = None
    sb_buffer = None        # Buffer for sub-negotiations

    # Default state variables
    got_iac = False     # Are we inside an IAC sequence?
    got_cmd = None      # Did we get a telnet command?
    got_sb = False      # Are we inside a subnegotiation?
    options = None      # Mapping for up to 256 TelnetOptions
    echo = False        # Echo input back to the client?
    _supress_echo = False   # Override echo option (control with supress_echo)
    terminal_type = None    # Negotiated telnet type
    columns = 80        # Number of columns on terminal
    rows = 50           # Number of rows on terminal

    # Attributes to be serialised that don't need special pickling
    # Other attrs to be serialised: socket, options
    # Can't pickle: handler
    SERIALISE_ATTRS = [
        'got_iac', 'got_cmd', 'got_sb', 'echo', '_supress_echo',
        'sb_buffer', 'terminal_type', 'columns', 'rows',
    ]

    # Buffers
    def __init__(self, *args, **kwargs):
        super(ProtocolTelnet, self).__init__(*args, **kwargs)
        self.options = defaultdict(TelnetOption)
        self.sb_buffer = Buffer()

    def connect(self):
        # Start telnet negotiation (unless in raw mode)
        if not self.settings.socket_raw:
            self._tn_request(DO, TTYPE)     # Get terminal type
            self._tn_request(DO, NAWS)      # Do NAWS - find window size

    def read(self, data):
        return data

    def write(self, *data, **kwargs):
        for bytestring in data:
            if not isinstance(bytestring, six.binary_type):
                raise ValueError('Raw protocol can only send a byte string')
            self.client.send_buffer = bytestring

    def serialise(self):
        data = {attr: getattr(self, attr) for attr in self.SERIALISE_ATTRS}
        data['options'] = {
            key: val.serialise()
            for key, val in self.options.items()
        }
        return data

    def deserialise(self, data):
        # Deserialise all standard attrs
        for key in self.SERIALISE_ATTRS:
            if key not in data:
                self.service.log.client('Serialised protocol missing %s' % key)
                continue
            if isinstance(getattr(self, key, None), Buffer):
                getattr(self, key).extend(data[key])
            else:
                setattr(self, key, data[key])

        self.options = {
            key: TelnetOption(serialised=val)
            for key, val in data['options'].items()
        }

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
            self.write(IAC + WILL + ECHO)
        else:
            self.write(IAC + WONT + ECHO)

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
            self._send_buffer.extend(data)

        # Add data to recv_buffer
        self._recv_buffer.extend(data)
        if (
            self.settings.client_buffer_size
            and len(self._recv_buffer) > self.settings.client_buffer_size
        ):
            self._recv_buffer.clear()
            self.write('Input too long')

        # Standardise inbound line endings
        # RFC 854 says \r on its own is not allowed
        self._recv_buffer = self._recv_buffer.replace(
            b'\r\n', b'\n',
        ).replace(
            b'\r\0', b'\n'
        )

        # Test for a complete line
        if not b'\n' in self._recv_buffer:
            return None

        # Pull off first line
        (line, self._recv_buffer) = self._recv_buffer.split(b'\n', 1)
        line = line.decode('utf-8', 'replace')
        return line