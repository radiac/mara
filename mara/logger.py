"""
Logging class for Mara
"""
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import datetime


# Log verbosity constants
NONE        = ''
ALL         = 'all'
ANGEL       = 'angel'
SERVICE     = 'service'
SERVER      = 'server'
CLIENT      = 'client'
EVENT       = 'event'
STORE       = 'store'
DEBUG       = 'debug'
DEFAULT_LEVELS = ['angel', 'server']

class Logger(object):
    def __init__(self, settings):
        """
        Determine which log levels to listen to, and open log file
        """
        # Get settings
        self.settings = settings
        levels = settings.log
        self.filename = settings.get_path('log_file')
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
            self.levels = []
            self.exclude = []
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
        except IOError as e:
            print("Error opening logfile: %s" % e, file=sys.stderr)
            self.disabled = True
        
        # Pre-calculate prefix
        self.update_prefix()
    
    def ignore_angel(self):
        """
        Ignore the angel level
        """
        self.exclude.append(ANGEL)
    
    def force_with_pid(self):
        """
        Set with_pid to True, unless with_pid is False
        """
        if self.with_pid is None:
            self.with_pid = True
            self.update_prefix()

    def update_prefix(self):
        """
        Pre-calculate prefix settings
        """
        # Re-calculate with_level==None - levels may have changed
        if self.settings.log_level is None:
            if len(self.levels) == 1:
                self.with_level = False
            else:
                self.with_level = True
        
        # Generate as much of the prefix as possible
        self.prefix = ''
        if self.with_pid or (self.filename and self.with_pid is None):
            self.prefix = '[%s] ' % os.getpid()
        elif not self.filename and not self.with_level:
            # If printing to stdout, start each line with a *
            self.prefix = '* '
        
    def write(self, level, *lines):
        """
        Filter by level before writing lines to the log file
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
            prefix = '%s%s> ' % (prefix, level)
        lines = ['%s%s' % (prefix, line) for line in lines]
        
        self._write(lines)
    
    def _write(self, lines):
        """
        Perform actual write, without filtering or processing
        """
        # See if printing to STDOUT
        if not self.file:
            print("\n".join(lines))
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
    def angel(self, *lines):
        self.write(ANGEL, *lines)
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


class AngelLogger(Logger):
    """
    Logger which writes to the angel
    """
    def __init__(self, settings, angel):
        self._angel = angel
        super(AngelLogger, self).__init__(settings)
        
        # Angel always logs with pid
        self.force_with_pid()
        
    def open(self):
        "Nothing to open"
    
    def close(self):
        "Nothing to close"
    
    def _write(self, lines):
        self._angel.log(lines)
