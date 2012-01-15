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
PLUGIN      = 3
CLIENT      = 4
EVENT       = 5
DEBUG       = 6

help_verbosity = '''
0 = No logging
1 = Manager (start, stop)
2 = Server (start, stop)
3 = Plugin registry (load, error)
4 = Event registry (listen, unlisten)
5 = Client (connect, disconnect)
6 = Debug messages (event calls)
'''

class Logger(object):
    def __init__(self):
        """
        Initialise
        """
        # Start disabled, so open() will not close()
        self.file = None
        self.prefix = ''
        
    def open(self):
        """
        Open or re-open the log file
        Call this if:
            * the verbosity level changes from or to NONE
            * the process ID changes
        """
        # Close the logfile, if logger is enabled
        self.close()
        
        # Disable
        if settings.verbosity == NONE:
            # This logger is supposed to be turned off
            return
        
        # See if printing to STDOUT
        if settings.debug:
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
        if level > settings.verbosity:
            return
        
        # Add pid prefix
        prefix = self.prefix
        if settings.log_timestamp:
            # Format as close to syslog as possible
            prefix = datetime.datetime.today().strftime('%b %d %X') + " " + prefix
            lines = [prefix + line for line in lines]
        
        
        # See if printing to STDOUT
        if not self.file:
            print "\n".join(lines)
            return
        
        # Write lines
        self.file.write("\n".join(lines) + "\n")
        self.file.flush()
    
    def close(self):
        """
        Close the log file
        """
        if self.file:
            self.file.close()
    
    def __del__(self):
        """
        Clean up
        """
        # The log file should get closed by file.__del__, but just in case
        self.close()
        

# Initialise logger
logger = Logger()

def init():
    """
    Initialise the logger
    """
    logger.open()

def logger_factory(level):
    def fn(*lines):
        logger.write(level, *lines)
    return fn

manager = logger_factory(MANAGER)
server = logger_factory(SERVER)
plugin = logger_factory(PLUGIN)
client = logger_factory(CLIENT)
event = logger_factory(EVENT)
debug = logger_factory(DEBUG)
