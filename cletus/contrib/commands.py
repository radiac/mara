"""
Cletus commands
"""
import re

from collections import defaultdict
from ... import events
from ... import util

__all__ = [
    'CommandRegistry', 'Command', 'CommandEvent', 'cmd_commands',
    'RE_WORD', 'MATCH_WORD', 'RE_STR', 'MATCH_STR', 'RE_LIST', 'MATCH_LIST',
]


# Match a word
RE_WORD = r'(\w+)'
MATCH_WORD = r'^' + RE_WORD + '$'

# Match a string
RE_STR = r'(.*?)'
MATCH_STR = r'^' + RE_STR + '$'

# Match a list of strings, separated by commas or "and"
RE_LIST = r'(.*?)(?:(?:\s*,\s*|\s+and\s+)(.*?))*'
MATCH_LIST = r'^' + RE_LIST + '$'


class CommandRegistry(object):
    def __init__(self, service):
        self.service = service
        self.commands = {}
        self.groups = defaultdict(list)
        
        # Bind event handlers
        service.listen(events.Receive, self.receive)
        service.listen(events.PostStart, self.sort_groups)
        service.listen(events.PostRestart, self.sort_groups)
    
    def register(self, name, fn=None, **kwargs):
        """
        Register a command
        """
        # Can take multiple argument combinations
        if isinstance(name, Command):
            # Passed a Command instance
            #   cmd.register(Command('name', ..))
            self._register_command(name)
            return name
        
        # Or could be used as a decorator without arguments
        #   @cmd.register
        #   def mycmd(..)
        elif callable(name):
            fn = name
            name = name.__name__
        
        # Called with pre-defined fn
        #   @command(..)
        #   def mycmd(..): pass
        #   cmd.register('name', mycmd)
        if hasattr(fn, 'command_kwargs'):
            new_kwargs = {}
            new_kwargs.update(fn.command_kwargs)
            new_kwargs.update(kwargs)
            kwargs = new_kwargs
        
        
        # Closure to register with args and kwargs
        def closure(fn):
            # Build command and register
            cmd = Command(self, name, fn, **kwargs)
            self._register_command(cmd)
            
            # Return original fn
            return fn
        
        # Called without args needs to register immediately
        if fn:
            closure = closure(fn)
        
        # Called with args, need to return the closure to operate on the fn
        #   @cmd.register('name')
        #   def mycmd(..)
        return closure
    
    def _register_command(self, cmd):
        "Register a command instance"
        self.commands[cmd.name] = cmd
        self.groups[cmd.group].append(cmd)
        
    def receive(self, event):
        """
        Handle a Receive event
        """
        # Hijack event
        event.stop()
        
        # Parse command
        try:
            cmd, raw_args = self.parse(event)
        except ValueError as err:
            event.client.write(err)
            return
        
        # Run command
        # ++ support generator
        self.commands[cmd].call(event, cmd, raw_args)
    
    def parse(self, event):
        """
        Parse the data from a Receive event into a command name and raw args,
        and check that it is a valid command.
        
        Raise ValueError if the command was not recognised or available; the
        error message will be sent back to the client.
        """
        # Split command and raw data
        data = event.data.strip()
        if ' ' in data:
            cmd, raw_args = data.split(' ', 1)
        else:
            cmd, raw_args = data, ''
        
        # Check command exists
        if cmd not in self.commands:
            raise ValueError('That command was not recognised')
        
        return cmd, raw_args.strip()
    
    def sort_groups(self, event):
        """
        Order each group's commands by name
        """
        for name in self.groups.keys():
            self.groups[name].sort(key=lambda cmd: cmd.name)


class Command(object):
    """
    A command class manages how data is parsed and the command function is
    called. It will be passed whatever keyword arguments are sent to
    ``registry.register()``. A command class can be used for multiple commands.
    
    This command class parses arguments based on the regular expression in
    ``args``.
    """
    def __init__(
        self, registry, name, fn,
        args=None, syntax=None, group=None, help=None, context=None,
    ):
        """
        Build a command
            registry    Command registry
            name        Name of command
            fn          Function to call to perform the command
            args        Optional regular expression to match arguments
            syntax      Optional human-readable syntax
            group       Optional command group
            help        Optional help; if missing, will be taken from docstring
            context     Optional object to set as CommandEvent.context
        """
        self.registry = registry
        self.name = name
        self.fn = fn
        self.group = group
        self.syntax = syntax
        self.help = help if help is not None else fn.__doc__.strip()
        self.context = context
        
        if args:
            args = re.compile(args)
        self.args = args
        
    def call(self, event, cmd, raw_args):
        """
        Parse the input from the command and call the command function
        
        Arguments:
            event       The Receive event
            cmd         The command that triggered this call
            raw_args    The raw arguments after the command
        """
        try:
            args, kwargs = self.parse(raw_args)
        except ValueError as err:
            event.client.write(err)
            return
        
        # Build CommandEvent
        cmd_event = CommandEvent(
            event.client, event.data, cmd, self, self.registry, self.context
        )
        
        try:
            self.fn(cmd_event, *args, **kwargs)
        except Exception as err:
            # Log and report back to the user
            report = ['Command failed: %s' % err]
            details = util.detail_error()
            self.registry.service.log.write('command', *(report + details))
            if self.registry.service.settings.commands_debug:
                report.append(util.HR('Traceback'))
                report.extend(details)
                report.append(util.HR())
            event.client.write(*report)
    
    def parse(self, data):
        """
        Parse the arguments
        """
        # Test for no args
        if not self.match:
            if data:
                raise ValueError("Syntax: %s" % self.name)
            else:
                return None
        
        # Try to match
        matches = self.args.search(data)
        if not matches:
            raise ValueError("Syntax: %s %s" % (self.name, self.syntax))
        
        # Parse arguments types
        return matches.groups(), matches.groupdict()


class CommandEvent(events.Receive):
    """
    Command event
    """
    def __init__(self, client, data, match, command, registry, context):
        super(CommandEvent, self).__init__(client, data)
        self.match = match
        self.command = command
        self.registry = registry
        self.context = context

    def __str__(self):
        # Only show the command used - skip Receive and call its parent
        return super(events.Receive, self).__str__() + ': %s' % self.match


def command(**kwargs):
    """
    A wrapper to define a command's arguments before the registry command name
    are known
    """
    def closure(fn):
        fn.command_kwargs = kwargs
    return closure


@command(args=r'^(?P<group>\w+)?$', syntax="(groups|<group>)")
def cmd_commands(event, group=''):
    """
    List commands
    """
    groups = event.registry.groups
    if group == 'groups' or group not in groups:
        event.client.write('Valid groups are: %s' % ', '.join(
            [name or '(None)' for name in groups.keys()]
        ))
        return
    
    groupname = ''
    if group:
        groupname = group.title() + ' '
    
    lines = [util.HR('%sCommands' % groupname)]
    lines.extend([
        '%s\t%s%s' % (cmd.name, cmd.syntax)
        for cmd in groups[group]
    ])
    lines.append(util.HR())
    event.client.write(*lines)

@command(
    args=r'^(?P<cmd>\w+)?$', syntax="<command>",
    help="Show help for a command",
)
def cmd_help(event, cmd=None):
    """
    Show help for a command
    
    Pass context={'commands': 'name of cmd_commands command'} to make the
    syntax error message more helpful.
    Recommend that registration overrides syntax with a reference to the 
    commands command, eg '<command>, or type "commands" to see a list of commands'
    """
    # Helpful syntax error
    if cmd is None:
        msg = 'Syntax: %s %s' % (event.match, event.command.syntax)
        if event.context and 'cmd_commands' in event.context:
            msg += ', or type %s to see a list of commands' % (
                event.context['cmd_commands']
            )
        event.client.write(msg)
        return
    
    # Look up command
    command = event.registry.commands.get(cmd)
    if command is None:
        event.client.write('Unknown command')
    
    event.client.write(
        util.HR('Help: %s' % command.name),
        command.help,
        util.HR()
    )
