"""
Default settings
"""

#
# General
#

# Root path for all relative paths defined in settings
# If None, paths will be relative to the service script
root_path = None


#
# Server
#

# IP to listen on
# Set to '' for all
# Override with --host=HOST
host = '127.0.0.1'

# Port to listen on
# Override with --port=PORT
port = 9000

# Raw socket mode
# If true, disable telnet mode: perform no telnet negotiation, do not buffer
# inbound data, and do not modify outbound data.
# If false, enable telnet mode: perform telnet negotiation, buffer inbound data
# until newline \r\n is received, and concat and suffix outbound data with \r\n
socket_raw = False

# Socket activity timeout
# How long to wait for socket activity before polling, in seconds
# This needs to be low enough for any timed polling activity (game ticks etc)
socket_activity_timeout = 0.1

# Size of socket buffer
socket_buffer_size = 1024

# Internal buffer size for client
# Maximum length of a single line of input
# Set to 0 for no limit
client_buffer_size = 10240

# Keepalive
socket_keepalive = True

# Timeout for a client socket
# After this many seconds of inactivity, the client will be disconnected
# Set to 0, None or falsey value to have no timeout
socket_timeout = None


#
# Store
#

# Store folder
# By default, Store objects will save their data to json files in this folder
# If it is not an absolute path, Mara will use the root_path setting
store_path = 'store'


#
# Flash socket support
#

# How long to wait for a flash cross-domain policy request, in seconds
# No data will be sent to the client before then
# Set to 0, None or falsey value to disable Flash policy
# Set this too low and Flash may not request in time, causing a security error
# Set this too high and your clients will have a noticeable delay before
# getting their prompt.
# When possible, set flash_wait=False and serve policy requests on port 843
#flash_wait = 0.5
flash_wait = None

# Flash cross-doman policy
# Note: You may need to change to-ports
flash_policy = """<?xml version="1.0" encoding="UTF-8"?>
<cross-domain-policy xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://www.adobe.com/xml/schemas/PolicyFileSocket.xsd">
    <allow-access-from domain="*" to-ports="9000" secure="false" />
</cross-domain-policy>
\0"""



#
# Logging
#

# Log levels to listen to
# Set to a list of log levels, or a comma separated list of log levels
# Set to 'all' to log everything
# Set to True to log default levels
# Set to None or falsey value to log nothing
log = True

# Path to logfile
# Set to None or falsey value to log to stdout (or pass --no-log_file)
# If it is not an absolute path, Mara will use the root_path setting
log_file = None

# Show the pid on each log line?
#   None    Show it in log files but not stdout
#           Always show when run with angel
#   True    Show it all the time
#   False   Never show it
log_pid = None

# Show the time on each log line?
#   None    Show it in log files but not stdout
#   True    Show it all the time
#   False   Never show it
log_time = None

# Show the log level on each log line?
#   None    Show it if more than one level
#           'angel' level only counts if it's run with angel
#   True    Show it all the time
#   False   Never show it
log_level = None


#
# Angel settings
#

# Angel socket family - changes what type of socket the angel uses
# If set to 'AF_UNIX' it will use a unix socket
# Set to 'AF_INET' for a TCP socket
angel_family = 'AF_UNIX'
#angel_family = 'AF_INET'

# Socket for communication with the angel
# * If family is AF_UNIX, this should be the path to the unix socket
#   If it is not an absolute path, Mara will use the root_path setting
# * If family is AF_INET, this should be a tuple of (ip, port)
angel_socket = 'angel.sock'
#angel_socket = ('127.0.0.1', 9001)

# Auth key for the angel socket
angel_authkey = '1234567890'


#
# Misc settings
#

# Collect settings from command line arguments
# If False, do not collect from command line
settings_collect_args = True

# Character sequence to use for styles.hr
hr_sequence = '-'

# Base State instance for styles.hr
hr_state = None
# For bold red lines:
#from .. import styles as _styles
#hr_state = _styles.State(_styles.RED, _styles.BOLD)


#
# contrib.comments
#

# If a command fails, send debug trace to the client
commands_debug = True
