"""
Command registry
"""

import re

from cletus.user import User

# Store global commands in a dict
commands = {}
publics['commands'] = commands

# Keep track of command groups
groups = {}

class ArgException(Exception): pass

RE_MANY = '(?:\s*,\s*|\s+and\s+)'

class Arg(object):
    """
    Command argument
    """
    def __init__(self, name, match, syntax=None, optional=False, many=None):
        """
        Arguments:
            name        Name of argument
            match       What to match:
                            "re"    A manual regular expression
                            str     A string - equivalent to ".+?"
                            Class   Uses Class.arg_match
            syntax      Optional; defaults to name
            optional    If True, this argument is optional
            many        If True, this argument can be specified multiple times
                        The result will always be a list
        Note: any regex parens must be (?:...) instead of (...), to avoid
            messing up list parsing
        """
        # ++ Add match support for list of options, for OR (eg User OR str)
        self.name = name
        self.match = match
        self.syntax = syntax or "<%s>" % name
        self.optional = optional
        self.many = many
        
        # Get the regular expression for the match element
        re_full = self._re_el()
        self.re_el = re_full
        
        # Build it into a full re for the arg
        # Will not take account of optional
        if self.many:
            re_full = r'%s(%s%s)*' % (re_full, RE_MANY, re_full)
        re_full = r'(?P<%s>%s)' % (name, re_full)
        self.re = re_full
        
        # Build the argument parser
        if self.many:
            re_parse = r'^(%s)(?:%s(%s))*$' % (self.re_el, RE_MANY, self.re_el)
            self.re_parse = re.compile(re_parse)
        else:
            self.re_parse = None
        
    def _re_el(self):
        """
        Get the regular expression for match
        """
        # Plain string is a regular expression
        if isinstance(self.match, str):
            return self.match
        
        # It could be an object which defines its own match, like User
        if hasattr(self.match, 'arg_match'):
            return self.match.arg_match
        
        # Otherwise, as much of as little as possible    
        return r'.+?'
    
    def parse(self, matched):
        """
        Parse a matched string into a suitable response
        """
        if not self.many:
            return self._parse_el(matched)
        
        results = []
        
        # Match
        matches = self.re_parse.search(matched)
        if not matches:
            # This should never happen, but better this than raise and die
            raise ArgException('Internal error: the %s argument could not be parsed' % self.name)
        matches = matches.groups()
        # Catch single match
        if len(matches) == 2 and matches[1] == None:
            matches = matches[:1]
        
        # Parse each match
        for match in matches:
            results.append( self._parse_el(match) )
        
        return results

    def _parse_el(self, data):
        if self.match == User:
            target = find_user(data)
            if not target:
                raise ArgException('There is nobody here called %s' % data)
            return target
            
        return data

publics['Arg'] = Arg

class CommandArguments(object):
    """
    Command arguments, parsed from the command line
    """
    def __init__(self, kwargs):
        for kwarg, val in kwargs.items():
            setattr(self, kwarg, val)

class Command(object):
    """
    A command
    """
    def __init__(self, name, fn, args=None, group=None):
        """
        Build a command
            name        Name of command
            fn          Function to call to perform the command
            args        List of (arg_name, match) tuples to type check
                        The arg_name must be unique within a command
                        Match values:
                        If args==None, no arguments allowed
            group       Command group
        """
        self.name = name
        self.fn = fn
        self.group = group
        
        # Catch no arguments
        if not args:
            self.args = None
            self.match = None
            self.syntax = ''
            return
        
        # Process arguments
        self.args = []
        re_args = []
        syntax = []
        count = len(args)
        for i, arg in enumerate(args):
            
            # Ensure all args are Arg instances
            if isinstance(arg, (tuple, list)):
                arg = Arg(*arg)
            elif not isinstance(arg, Arg):
                arg = Arg(arg.__name__, arg)
            
            # Add to arg list
            self.args.append(arg)
            
            # Add whitespace
            arg_re = arg.re
            if arg.optional:
                if i + 1 < count:
                    arg_re = r'(%s\s+)?' % arg_re
                else:
                    arg_re += '?'
            
            # Add to lists
            re_args.append(arg_re)
            if arg.optional:
                syntax.append('[%s]' % arg.syntax)
            else:
                syntax.append(arg.syntax)
            
        
        # Build match re and syntax string
        self.match = re.compile('^' + ''.join(re_args) + '$')
        self.syntax = ' '.join(syntax)
        
    def call(self, e):
        """
        Parse the input the command
        """
        args = self.parse(e)
        if args == False:
            return
            
        e.args = args
        
        try:
            self.fn(e)
        except Exception, err:
            details = util.detail_error()
            report = ['Command failed: %s' % err]
            if e.user.store('profile')['debug']:
                report.append(util.HR('Traceback'))
                report.extend(details)
                report.append(util.HR())
            e.user.write(*report)
            
    
    def parse(self, e):
        """
        Parse the arguments
        """
        # Test for no args
        if not self.match:
            if e.input:
                e.user.write("Syntax: %s" % self.name)
                return False
            else:
                return None
        
        # Try to match
        matches = self.match.search(e.input)
        if not matches:
            e.user.write("Syntax: %s %s" % (self.name, self.syntax))
            return False
        
        # Parse arguments types
        data = matches.groupdict()
        for arg in self.args:
            # Optional args
            if not data[arg.name]:
                continue
            
            # Parse
            try:
                data[arg.name] = arg.parse(data[arg.name])
            except ArgException, err:
                e.user.write("%s" % err)
                return False
            
        return CommandArguments(data)


# Command decorator
@public
def command(name, *args, **kwargs):
    # Catch if this has been called without args
    fn = None
    if hasattr(name, '__call__'):
        fn = name
        name = name.__name__
        
    # Has been passed args, make a closure
    def closure(fn):
        # Build command
        cmd = Command(name, fn, *args, **kwargs)
        
        # Register
        commands[name] = cmd
        if not groups.has_key(cmd.group):
            groups[cmd.group] = []
        groups[cmd.group].append(cmd)
        
        # Return original fn
        return fn
    
    # Without args needs to register immediately
    if fn:
        closure = closure(fn)
    
    return closure

@command('commands', args=[Arg('group', '\w+', optional=True, syntax="(groups|<group>)")])
def cmd_commands(e):
    group = e.args.group
    if group == 'groups' or not groups.has_key(group):
        e.user.write('Valid groups are: %s' % ', '.join(
            [name or '(None)' for name in groups.keys()]
        ))
        return
    
    groupname = ''
    if group:
        groupname = group[0].upper() + group[1:] + ' '
    
    lines = [util.HR('%sCommands' % groupname)]
    lines.extend(['%s\t%s' % (cmd.name, cmd.syntax) for cmd in groups[group]])
    lines.append(util.HR())
    e.user.write(*lines)

@listen('init')
def sort_groups(e):
    """
    Sort command groups
    """
    for name, group in groups.items():
        groups[name].sort(key=lambda cmd: cmd.name)
