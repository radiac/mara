"""
Logging class for Cletus
"""

import os
import sys
import datetime

import settings

# Log verbosity constants
NONE        = 0
MANAGER     = 1
SERVER      = 2
CLIENT      = 3

help_verbosity = '''
0 = No logging
1 = Manager events (start, stop)
2 = Server events (start, stop)
3 = Client events (connect, disconnect)
'''

class Logger(object):
    def __init__(self, disabled=False):
        """
        Initialise
        """
        # Start disabled, so open() will not close()
        self.disabled = True
        self.prefix = ''
        
    def open(self, disabled=False):
        """
        Open or re-open the log file
        Call this if:
            * the verbosity level changes from or to NONE
            * the process ID changes
        """
        # Close the logfile, if logger is enabled
        self.close()
        
        # Disable
        self.disabled = True
        if disabled:
            # This logger is supposed to be turned off
            return
        
        # Try to enable
        try:
            self.file = open(settings.logfile, 'a')
            self.disabled = False
        except IOError, e:
            print >> sys.stderr, "Error opening logfile: %s" % e
        
        # Pre-calculate as much of the prefix as possible
        self.prefix = ''
        if settings.log_pid:
            self.prefix = '[%s] ' % os.getpid()
            
    def write(self, level, *lines):
        """
        Write lines to the log file
        """
        # Skip if disabled, or verbosity says no
        if self.disabled or level > settings.verbosity:
            return
        
        # Add pid prefix
        prefix = self.prefix
        if settings.log_timestamp:
            # Format as close to syslog as possible
            prefix = datetime.datetime.today().strftime('%b %d %X') + " " + prefix
            lines = [prefix + line for line in lines]
        
        # Write lines
        self.file.write("\n".join(lines) + "\n")
        self.file.flush()
    
    def close(self):
        """
        Close the log file
        """
        if self.disabled:
            return
        self.file.close()
    
    def __del__(self):
        """
        Clean up
        """
        # The log file should get closed by file.__del__, but just in case
        self.close()
        

# Initialise logger; disable if verbosity == NONE
logger = Logger( disabled=(settings.verbosity == NONE) )

def init():
    """
    Initialise the logger
    """
    logger.open()

def manager(*lines):
    """
    Log a manager event
    """
    logger.write(MANAGER, *lines)

def server(*lines):
    """
    Log a server event
    """
    logger.write(SERVER, *lines)

def client(*lines):
    """
    Log a client event
    """
    logger.write(CLIENT, *lines)

