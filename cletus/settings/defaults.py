"""
Default settings
"""

#
# Connection
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

# Internal buffer size
# Maximum length of a single line of input
# Set to 0 for no limit
internal_buffer_size = 10240

# Keepalive
socket_keepalive = True


#
# Timeouts
#

# Timeout for a client socket
# After this many seconds of inactivity, the client will be disconnected
# Set to 0, None or falsey value to have no timeout
socket_timeout = None


#
# Store
#

# Store folder
# By default, Store objects will save their data to json files in this folder
store_path = 'store'


#
# Flash socket support
#

# Flash support
# Will provide the cross-domain policy below on request
# Note: Will cause a delay of flash_wait seconds for new non-Flash connections
# To avoid a delay, set flash=False and serve policy requests on port 843
flash = True

# Flash wait
# How long to wait for Flash to send the policy request, in seconds
# No data will be sent to the client before then
# Set this too low and Flash may not request in time, causing a security error
# Set this too high and your clients will not get their prompt
# Note: This will be tested each poll, so depends on socket_activity_timeout
flash_wait = 0.5

# Flash cross-doman policy
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
log_file = None

# Show the pid on each log line?
#   None    Show it in log files but not stdout
#   True    Show it all the time
#   False   Never show it
log_pid = None

# Show the time on each log line?
#   None    Show it in log files but not stdout
#   True    Show it all the time
#   False   Never show it
log_time = None

# Show the log level on each log line?
#   True    Show it all the time
#   False   Never show it
log_level = True


#
# contrib.comments
#

# If a command fails, send debug trace to the client
commands_debug = True
