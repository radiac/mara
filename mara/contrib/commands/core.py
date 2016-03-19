"""
Mara commands
"""
from __future__ import unicode_literals

import inspect
import re

from collections import defaultdict
from ... import events
from ... import util
from ... import styles

__all__ = [
    'CommandRegistry', 'Command', 'CommandEvent', 'define_command',
    'RE_WORD', 'MATCH_WORD', 'RE_STR', 'MATCH_STR', 'RE_LIST', 'MATCH_LIST',
]


# Match a word
RE_WORD = r'(\w+)'
MATCH_WORD = r'^' + RE_WORD + '$'

# Match a string
RE_STR = r'(.*?)'
MATCH_STR = r'^' + RE_STR + '$'

# Match a list of words, separated by commas
RE_LIST = r'(.*?(?:\s*,\s*\S*?)*)'
MATCH_LIST = r'^' + RE_LIST + '$'


class CommandEvent(events.Client):
    """
    Command event
    """

    def __init__(
        self, client, data, match, args, kwargs, command, registry, context,
    ):
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
        event_str = super(events.Client, self).__str__().strip()
        return '%s: %s' % (event_str, self.match)


class CommandRegistry(object):
    def __init__(self, service):
        self.service = service
        self.commands = {}
        self.aliases = []
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
        if callable(name):
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
            cmd = Command(name, fn, **kwargs)
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
        cmd.registry = self
        self.commands[cmd.name] = cmd
        self.groups[cmd.group].append(cmd)

    def unregister(self, name):
        """
        Unregister the named command
        """
        # Remove from command list
        cmd = self.commands.pop(name, None)

        # Remove from group
        cmd_group = self.groups[cmd.group]
        del cmd_group[cmd_group.index(cmd)]

    def extend(self, name, mixin):
        """
        If the command is a Handler, extend it with this mixin
        """
        if name not in self.commands:
            raise ValueError('Unknown command')
        command = self.commands[name]
        if not isinstance(command.fn, events.Handler):
            raise TypeError('Cannot extend %s, not a Handler command' % name)
        if isinstance(command.fn, mixin):
            raise ValueError('Cannot extend %s, already has this mixin' % name)
        command.fn.extend(mixin)

    def alias(self, match, replace):
        """
        Define a command alias

        Matches will be evaluated in order they are defined, before commands
        are checked.

        The ``replace`` argument can include backreferences; the arguments will
        be used with re.sub, equivalent to::

            input = re.sub(match, replace, input)

        Examples::

            commands.alias(r'^s$', 'south')
            commands.alias(r'^;', 'emote ')
            commands.alias(r'^!(\S+?) (.*)$', r'emote shouts at \1: \2')
        """
        match = re.compile(match, re.IGNORECASE)
        self.aliases.append((match, replace))

    def handle_receive(self, event):
        """
        Handle a Receive event
        """
        # Hijack event
        event.stop()

        # Run aliases
        for match, replace in self.aliases:
            event.data = match.sub(replace, event.data)

        # Parse command
        try:
            cmd, raw_args = self.parse(event)
        except ValueError as err:
            event.client.write(str(err))
            return

        # Run command
        self.commands[cmd].trigger(event, cmd, raw_args)

    def handle_command(self, event):
        """
        Handle a CommandEvent
        """
        try:
            if (
                inspect.isgeneratorfunction(event.command.fn) or
                isinstance(event.command.fn, events.Handler)
            ):
                # ++ python 3.3 has yield from
                generator = event.command.fn(
                    event, *event.args, **event.kwargs)
                try:
                    next(generator)
                except StopIteration:
                    pass
                else:
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
            event.command.registry.service.log.write(
                'command', *(report + details))
            if event.command.registry.service.settings.commands_debug:
                report.append(styles.hr('Traceback'))
                report.extend(details)
                report.append(styles.hr)
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
        if (
            cmd not in self.commands or
            not self.commands[cmd].is_available(event)
        ):
            raise ValueError('That command was not recognised')

        return cmd, raw_args.strip()

    def sort_groups(self, event):
        """
        Order each group's commands by name
        """
        for name in self.groups.keys():
            self.groups[name].sort(key=lambda cmd: cmd.name)

    def __contains__(self, name):
        return name in self.commands


class Command(object):
    """
    A command class manages how data is parsed and the command function is
    called. It will be passed whatever keyword arguments are sent to
    ``registry.register()``. A command class can be used for multiple commands.

    This command class parses arguments based on the regular expression in
    ``args``.
    """
    # Command registry is set by the registry during register().
    # If a subclass needs to take special actions after registration, replace
    # this with a property.
    registry = None

    # No bound fn class - means the fn argument is required by constructor
    fn = None

    def __init__(
        self, name,
        fn=None, args=None, syntax=None, group=None, help=None, can=None,
        context=None,
    ):
        """
        Build a command
            name        Name of command
            fn          Callable to perform the command - either a function, or
                        an event handler class. The handler class will be
                        instantiated if it is not already. If not provided,
                        it will look for a bound ``fn`` method on the command
                        class; if that doesn't exist it will raise a TypeError.
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
        self.name = name
        self.group = group
        self.syntax = syntax
        self.can = can

        # Instantiate an uninstantiated Handler class
        if fn:
            if isinstance(fn, events.handler.HandlerType):
                fn = fn()
            self.fn = fn
        elif not self.fn:
            raise TypeError(
                'Command classes require a fn argument, or a bound fn method',
            )

        # Find help
        if help is not None:
            self.help = help
        elif fn.__doc__:
            self.help = fn.__doc__.strip()
        else:
            self.help = ''
        self.context = context

        # Pre-compile arguments regex
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

    def trigger(self, event, cmd, raw_args):
        """
        Trigger a CommandEvent for this command

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
        args = []
        for key, val in kwargs.items():
            named[matches.span(key)] = val
        for i, val in enumerate(matches.groups()):
            span = matches.span(i + 1)
            if span not in named:
                args.append(val)

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
