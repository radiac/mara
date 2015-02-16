==============
cletus.contrib
==============

The ``contrib`` module contains functionality which isn't used by the core of
Cletus, but which can be useful when building your own services.


``cletus.contrib.commands``
===========================

This provides a ``Receive`` handler for parsing commands, a command registry,
and a decorator to register command functions.

Example usage:

    # Create a command registry
    # This will add its own Receive handler
    from cletus.contrib.commands import CommandRegistry, cmd_commands, cmd_help
    commands = CommandRegistry(service)
    
    # Register the ``commands`` command, to list registered commands
    commands.register('commands', cmd_commands)
    
    # Register the ``help`` command, to show help for registered commands
    # The extra context tells help what we've registered cmd_commands as
    commands.register('help', cmd_help, extra={'cmd_commands': 'commands'})
    
    # Start registering commands
    @commands.register('look')
    def cmd_look(event):
        client = event.client
        client.write('You look around')
        service.write_all('%s looks around' % client.username, exclude=client)


Registering commands
--------------------

Register a command with the ``CommandRegistry.register`` method:

    @commands.register
    def help(event):
        'Triggered when user sends "help" with no arguments'
    
    @commands.register('look', args=r'(.*)', group='room'):
    def cmd_look(event, *args, **kwargs):
        'Triggered when user sends "look" with matching arguments'

Commands written outside the scope of the command registry (and before their
name is known) can have their parameters pre-defined with the ``@command``
decorator:

    from cletus.contrib.commands import command
    @command(args=r'(.*)')
    def dance(event, desc):
        ...
    
    # Register dance() as "prance" command
    commands.register('prance', dance)
    
    # Register dance() as "dance" command (take name of fn name)
    commands.register(dance)

This technique is used by other ``contrib`` modules, and can be useful when
defining your own re-usable modules.

The exact arguments for the ``register`` method depend on which class of
``Command`` you're using, but the default ``Command`` accepts the following
keyword arguments:
   
:   args:       Optional regular expression to match arguments
    syntax:     Optional human-readable syntax
    group:      Optional command group
    help:       Optional help; if missing, will be taken from docstring
    context:    Optional object to set as CommandEvent.context


Command functions
-----------------

Command functions are passed a ``CommandEvent`` with the data from the
``Receive`` event, plus:

``event.cmd``:          The command name which was matched for this command
``event.registry``:     The command registry this command is registered with


Subclassing the ``CommandRegistry``
-----------------------------------

By default ``CommandRegistry.parse`` splits received data into command and data
on the first space. This is the basis of a command syntax for talkers and muds.

You can change this behaviour by subclassing the registry and implementing your
own ``parse`` method. It receives the ``Receive`` event, and should return a
tuple of ``(command_name, command_raw_args)``, or raise a ``ValueError`` if the
command is not found or not available.


``cletus.contrib.rooms``
========================

This provides a ``Room`` store for keeping track of ``User`` objects.

It extends the ``User`` store with a ``room`` field.


