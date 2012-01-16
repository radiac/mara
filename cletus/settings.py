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

# Time to listen to the socket before polling other tasks
# Floating point number in seconds
listen_for = 1

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

# Timeout once the user has first connected
timeout_unnamed = datetime.timedelta(seconds=30)

# Timeout after the user has identified themselves (if user.name != None)
# Set to 0 for no limit
#timeout_named = datetime.timedelta(minutes=5)
timeout_named = 0


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
