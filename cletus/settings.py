"""
Cletus settings
"""

import datetime

#
# Connection
#

# IP to listen on
# Set to '' for all
# Override with --host=HOST
host = ''

# Port to listen on
# Override with --port=PORT
port = 9000

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
keepalive = True


#
# Timeouts
#

# Timeout for a client socket, in seconds
socket_timeout = 30

# Timeout for a user, in seconds
# Set to 0 for no limit
user_timeout = 0


#
# Flash socket support
#

# Flash support
# Will provide the cross-domain policy below on request
# Note: Will cause a delay of flash_wait seconds for new non-Flash connections
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
# Customisation
#

# Path to find plugins
#   None    No plugins will be loaded
#   str     Path to plugin file or dir
#   list    List of plugin files or dirs
# The list's order will be maintained
# When specifying files and dirs, normal name matching will not apply. Files
# will be loaded according to their filetype suffix:
#   .py     Plugin
#   .list   List of plugins to load now, relative to current path
plugins = None


#
# Logging
#

# Path to logfile
# Override with --logfile=PATH
logfile = 'cletus.log'

# Debug mode
# Logging is sent to STDOUT instead of the log file
debug = False

# Log verbosity
# See log.py for levels
# Override with --verbosity=LEVEL
verbosity = 0

# Log with process ID
log_pid = True

# Log with timestamp
log_timestamp = True
