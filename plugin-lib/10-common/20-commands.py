"""
Command registry
"""

import re

# Store global commands in a dict
commands = {}

# Command type args
ARG_USER = 1

class CommandArgs(object):
    """
    Command arguments
    """
    def __init__(self, kwargs):
        for kwarg, val in kwargs.items():
            setattr(self, kwarg, val)

class Command(object):
    """
    A command
    """
    def __init__(self, name, fn, args=None, syntax=None):
        """
        Build a command
            name        Name of command
            fn          Function to call to perform the command
            args        List of (arg_name, match) tuples to type check
                        The arg_name must be unique within a command
                        Match values:
                            User    Must be the name of a known User object
                            str     A string - equivalent to re .+?
                            "re"    A manual regular expression
                        If args==None, no arguments allowed
        """
        self.name = name
        self.fn = fn
        
        # Build match
        self.args_def = args
            
        if not args:
            self.match = None
            self.syntax = ''
        else:
            matches = []
            syntax = []
            
            for name, match in self.args_def:
                if isinstance(match, str):
                    re_match = match
                if match == ARG_USER:
                    re_match = '[a-zA-Z0-9]+'
                elif hasattr(match, 'arg_match'):
                    re_match = match.arg_match
                else:
                    re_match = '.+?'
                
                matches.append('(?P<%s>%s)' % (name, re_match))
                syntax.append('<%s>' % name)
                
            self.match = re.compile('^' + '\s+'.join(matches) + '$')
            self.syntax = ' '.join(syntax)
        
    def call(self, e):
        """
        Parse the input the command
        """
        args = self.parse(e)
        if args == False:
            return
            
        e.args = args
        self.fn(e)
    
    def parse(self, e):
        """
        Parse the arguments
        """
        # Test for no args
        if not self.match:
            if e.input:
                write(e.user, "Syntax: %s" % self.name)
                return False
            else:
                return None
        
        # Try to match
        matches = self.match.search(e.input)
        if not matches:
            write(e.user, "Syntax: %s %s" % (self.name, self.syntax))
            return False
        
        # Validate types
        data = matches.groupdict()
        for name, match in self.args_def:
            if match == ARG_USER:
                target = find_user(data[name])
                if not target:
                    write(e.user, 'There is nobody here called %s' % data[name])
                    return False
                data[name] = target
        
        return CommandArgs(data)
    

# Command decorator
def command(name, *args, **kwargs):
    def closure(fn):
        commands[name] = Command(name, fn, *args, **kwargs)
        return fn
    return closure
