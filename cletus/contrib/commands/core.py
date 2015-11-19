"""
Cletus commands
"""
import inspect
import re

from collections import defaultdict
from ... import events
from ... import util

__all__ = [
    'CommandRegistry', 'Command', 'CommandEvent', 'define_command',
    'cmd_commands', 'cmd_help', 'cmd_restart',
    'RE_WORD', 'MATCH_WORD', 'RE_STR', 'MATCH_STR', 'RE_LIST', 'MATCH_LIST',
    'RE_LIST_AND', 'MATCH_LIST_AND',
]


# Match a word
RE_WORD = r'(\w+)'
MATCH_WORD = r'^' + RE_WORD + '$'

# Match a string
RE_STR = r'(.*?)'
MATCH_STR = r'^' + RE_STR + '$'

# Match a list of strings, separated by commas
RE_LIST = r'(.*?)(?:\s*,\s*(.*?))*'
MATCH_LIST = r'^' + RE_LIST + '$'

# Match a list of strings, separated by commas or "and"
RE_LIST_AND = r'(.*?)(?:(?:\s*,\s*|\s+and\s+)(.*?))*'
MATCH_LIST_AND = r'^' + RE_LIST_AND + '$'


class CommandEvent(events.Client):
    """
    Command event
    """
    def __init__(self, client, data, match, args, kwargs, command, registry, context):
        super(CommandEvent, self).__init__(client)
        self.match = match
        self.args = args
        self.kwargs = kwargs
        self.command = command
        self.registry = registry
        self.context = context
        self.exception_fatal = False

    def __str__(self):
        # Just show the command used
        return super(events.Client, self).__str__() + ': %s' % self.match


class CommandRegistry(object):
    def __init__(self, service):
        self.service = service
        self.commands = {}
        self.groups = defaultdict(list)
        
        # Bind event handlers
        service.listen(events.Receive, self.handle_receive)
        service.listen(CommandEvent, self.handle_command)
        service.listen(events.PostStart, self.sort_groups)
    
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
        #   @define_command(..)
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
        
    def handle_receive(self, event):
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
        self.commands[cmd].call(event, cmd, raw_args)
    
    def handle_command(self, event):
        """
        Handle a CommandEvent
        """
        try:
            if inspect.isgeneratorfunction(event.command.fn):
                # ++ python 3.3 has yield from
                generator = event.command.fn(event, *event.args, **event.kwargs)
                generator.send(None)
                while True:
                    try:
                        try:
                            raw = yield
                        except Exception as e:
                            generator.throw(e)
                        else:
                            generator.send(raw)
                    except StopIteration:
                        break
                # ++ end python 2.7 support
            else:
                event.command.fn(event, *event.args, **event.kwargs)
        
        except Exception as err:
            # Log and report back to the user
            report = ['Command failed: %s' % err]
            details = util.detail_error()
            event.command.registry.service.log.write('command', *(report + details))
            if event.command.registry.service.settings.commands_debug:
                report.append(util.HR('Traceback'))
                report.extend(details)
                report.append(util.HR())
            event.client.write(*report)
            
            # Re-raise if exceptions should be fatal
            if event.exception_fatal:
                raise

    def parse(self, event):
        """
        Parse the data from a Receive event into a command name and raw args,
        and check that it is a valid available command.
        
        Raise ValueError if the command was not recognised or available; the
        error message will be sent back to the client.
        """
        # Split command and raw data
        data = event.data.strip()
        if ' ' in data:
            cmd, raw_args = data.split(' ', 1)
        else:
            cmd, raw_args = data, ''
        
        # Check command exists and is available
        if cmd not in self.commands or not self.commands[cmd].is_available(event):
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
        args=None, syntax=None, group=None, help=None, can=None,
        context=None,
    ):
        """
        Build a command
            registry    Command registry
            name        Name of command
            fn          Function to call to perform the command
            args        Optional regular expression to match arguments
                        (case insensitive)
            syntax      Optional human-readable syntax
            group       Optional command group
            help        Optional help; if missing, will be taken from docstring
            can         Optional callback to determine command availability.
                        It is passed the event, and if it returns True, the
                        command can be used. If not set, it can always be used.
            context     Optional object to set as CommandEvent.context
        """
        self.registry = registry
        self.name = name
        self.fn = fn
        self.group = group
        self.syntax = syntax
        self.can = can
        if help is not None:
            self.help = help
        elif fn.__doc__:
            self.help = fn.__doc__.strip()
        else:
            self.help = ''
        self.context = context
        
        if args:
            args = re.compile(args, re.IGNORECASE)
        self.args = args
    
    def is_available(self, event):
        """
        Given the event trying to access this command, determine if it is
        available.
        
        Defaults to yes.
        """
        if self.can:
            return self.can(event)
        return True
        
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
        
        # Build and trigger CommandEvent using the normal event system
        cmd_event = CommandEvent(
            event.client, event.data, cmd, args, kwargs,
            self, self.registry, self.context
        )
        self.registry.service.trigger(cmd_event)
    
    def parse(self, data):
        """
        Parse the arguments
        """
        # Test for no args
        if not self.args:
            if data:
                raise ValueError("Syntax: %s" % self.name)
            else:
                return ([], {})
        
        # Try to match
        matches = self.args.search(data)
        if not matches:
            raise ValueError("Syntax: %s %s" % (self.name, self.syntax))
        
        # Collect all keyword arguments for now
        kwargs = matches.groupdict()
        
        # Non-keyword arguments must be unnamed groups only
        # Thanks to http://stackoverflow.com/a/30293349/3301958
        named = {}
        unnamed = {}
        for key, val in kwargs.items():
            named[matches.span(key)] = val
        for i, val in enumerate(matches.groups()):
            span = matches.span(i + 1)
            if span not in named:
                unnamed[span] = val
        args = [unnamed[key] for key in sorted(unnamed.keys())]
        
        # Limit keyword arguments to just those with values
        # This will allow functions to specify defaults as normal
        kwargs = {key: val for key, val in kwargs.items() if val is not None}
        
        # Parse arguments types
        return args, kwargs


def define_command(**kwargs):
    """
    A wrapper to define a command's arguments before the registry command name
    are known
    """
    def closure(fn):
        fn.command_kwargs = kwargs
        return fn
    return closure


@define_command(args=r'^(?P<group>\w+)?$', syntax="(groups|<group>)")
def cmd_commands(event, group=None):
    """
    List commands
    """
    groups = event.registry.groups
    if group:
        if (group == 'groups' or group not in groups):
            event.client.write('Valid groups are: %s' % ', '.join(
                [name or '(None)' for name in groups.keys()]
            ))
            return
    
    groupname = ''
    if group:
        groupname = group.title() + ' '
    
    event.client.write(
        util.HR('%sCommands' % groupname),
        ' '.join(
            (cmd.name for cmd in groups[group] if cmd.is_available(event))
        ),
        util.HR(),
    )
    
@define_command(
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
    if command is None or not command.is_available(event):
        event.client.write('Unknown command')
        return
    
    syntax = 'Syntax: %s %s' % (command.name, command.syntax or '')
    
    if not command.help:
        event.client.write(syntax)
        return
    
    event.client.write(
        util.HR('Help: %s' % command.name),
        command.help,
        '', syntax,
        util.HR()
    )


@define_command(help="Restart the server")
def cmd_restart(event):
    event.exception_fatal = True
    event.service.write_all('-- Restarting server --')
    event.service.restart()
