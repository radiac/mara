"""
Logging class for Cletus
"""

import os
import sys
import datetime


# Log verbosity constants
NONE        = ''
ALL         = 'all'
SERVICE     = 'service'
SERVER      = 'server'
CLIENT      = 'client'
EVENT       = 'event'
STORE       = 'store'
DEBUG       = 'debug'
DEFAULT_LEVELS = ['server']

class Logger(object):
    def __init__(self, settings):
        """
        Determine which log levels to listen to, and open log file
        """
        # Get settings
        levels = settings.log
        self.filename = settings.log_file
        self.with_pid = settings.log_pid
        self.with_time = settings.log_time
        self.with_level = settings.log_level
        
        # Start disabled
        self.file = None
        self.prefix = ''
        self.disabled = True
        
        # Default levels
        if levels is True:
            levels = DEFAULT_LEVELS
        
        # If no levels, logging is disabled
        if not levels:
            return
        
        # See what to listen to and what to exclude
        if hasattr(levels, 'split'):
            levels = levels.split(',')
        self.levels = [level for level in levels if not level.startswith('-')]
        self.exclude = [level[1:] for level in levels if level.startswith('-')]
        
        if ALL in self.levels:
            self.levels = ALL
        if ALL in self.exclude:
            raise ValueError('Log level -all is not valid')
        
        # Now open logger
        self.disabled = False
        self.open()
        
    def open(self):
        """
        Open or re-open the log file
        
        Called automatically by constructor
        
        Call this if:
            * the verbosity level changes from or to NONE
            * the process ID changes
        """
        # Close the logfile, if logger is enabled
        self.close()
        
        # See if this logger is supposed to be turned off, or
        # if we're printing to STDOUT
        if self.disabled or not self.filename:
            return
        
        # Try to open file
        try:
            self.file = open(self.filename, 'a')
        except IOError, e:
            print >> sys.stderr, "Error opening logfile: %s" % e
            self.disabled = True
        
        # Pre-calculate as much of the prefix as possible
        self.prefix = ''
        if self.with_pid or (self.filename and self.with_pid is None):
            self.prefix = '[%s] ' % os.getpid()
        elif not self.filename:
            # If printing to stdout, start each line with a *
            self.prefix = '* '
            
    def write(self, level, *lines):
        """
        Write lines to the log file
        """
        # Skip if disabled, or unwanted log level
        if self.disabled or level in self.exclude or (
            self.levels != ALL and level not in self.levels
        ):
            return
        
        # Add pid prefix
        prefix = self.prefix
        if self.with_time or (self.filename and self.with_time is None):
            # Format as close to syslog as possible
            prefix = datetime.datetime.today().strftime('%b %d %X') + " " + prefix
        if self.with_level:
            prefix = '%s> %s' % (level, prefix)
        lines = ['%s%s' % (prefix, line) for line in lines]
        
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
    
    # Write aliases
    def service(self, *lines):
        self.write(SERVICE, *lines)
    def server(self, *lines):
        self.write(SERVER, *lines)
    def client(self, *lines):
        self.write(CLIENT, *lines)
    def event(self, *lines):
        self.write(EVENT, *lines)
    def store(self, *lines):
        self.write(STORE, *lines)
    def debug(self, *lines):
        self.write(DEBUG, *lines)
