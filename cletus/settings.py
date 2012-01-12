import datetime

#
# Connection
#

# Host and port to bind to
host = 'localhost'
port = 9000

# Default size of socket buffer
buffer_size = 1024

# Keepalive
keepalive = True

# Maximum number of connections at any one time
# Set to 0 to remove limit on trusted networks
# After this limit is reached, new connections will be refused
max_connections = 1000


#
# Timeouts
#

# Timeout once the user has first connected
timeout_connected = datetime.timedelta(seconds=30)

# Timeout after the user has identified themselves (if user.name != None)
timeout_user = datetime.timedelta(minutes=5)


#
# Logging
#

# Path to logfile
logfile = '/var/log/socketproxy.log'

# Log verbosity
# See log.py for levels
verbosity = 0

# Log with process ID
log_pid = True

# Log with timestamp
log_timestamp = True
