============
mara.contrib
============

The ``contrib`` module contains functionality which isn't used by the core of
Mara, but which can be useful when building your own services.


.. _module_contrib_commands:

``mara.contrib.commands``
=========================

This provides a ``Receive`` handler for parsing commands, a command registry,
and a decorator to register command functions.

Example usage::

    # Create a command registry
    # This will add its own Receive handler
    from mara.contrib.commands import CommandRegistry, register_cmds
    commands = CommandRegistry(service)
    
    # Register the standard commands
    register_cmds(commands)
    
    # Start registering custom commands
    @commands.register('look')
    def cmd_look(event):
        client = event.client
        client.write('You look around')
        service.write_all('%s looks around' % client.username, exclude=client)

If a command suffers an exception, it will be logged to the ``command`` log
level, and if ``settings.commands_debug`` is ``True``, it will also be sent
to the client who entered the command.

There are some standard commands that you may find useful:

    ``cmd_commands`` (eg ``commands``)
        List commands
    ``cmd_help`` (eg ``help <command>``)
        Show help for a command
    ``cmd_restart`` (eg ``restart``)
        Restart the service, maintaining existing connections. Requires the
        angel; probably best registered with a ``can`` permission argument
        (see :ref:`contrib_commands_register`).
    ``cmd_quit`` (eg ``quit``)
        Disconnect from the service

These can either be registered individually, eg::

    from mara.contrib.commands import cmd_commands
    commands.register('commands', cmd_commands)

Or they can be registered in bulk using default command names (see command
examples above)::

    from mara.contrib.commands import register_cmds
    register_cmds(commands)
    # Or if you are using mara.contrib.users.admin:
    register_cmds(commands, admin=True)


.. _contrib_commands_register:

Registering commands
--------------------

Register a command function with the ``CommandRegistry.register`` method::

    @commands.register
    def help(event):
        'Triggered when user sends "help" with no arguments'
    
    @commands.register('look', args=r'(.*)', group='room'):
    def cmd_look(event, *args, **kwargs):
        'Triggered when user sends "look" with matching arguments'

Commands written outside the scope of the command registry (and before their
name is known) can have their parameters pre-defined with the
``@define_command`` decorator::

    from mara.contrib.commands import define_command
    @define_command(args=r'(.*)')
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

``args``
    Optional regular expression to match arguments (case insensitive)
``syntax``
    Optional human-readable syntax
``group``
    Optional command group
``help``
    Optional help; if missing, will be taken from docstring
``can``
    Optional callback to determine command availability.
    It is passed the event, and if it returns True, the
    command can be used. If not set, it can always be used.
``context``
    Optional object to set as CommandEvent.context

A command can be unregistered with ``unregister(name)``::

    commands.unregister('prance')


.. _contrib_commands_functions:

Command functions
-----------------

Command functions are passed the following arguments:

``event``
    A ``CommandEvent`` based on the ``Receive`` event, (ie
    containing its ``service``, ``client`` etc), plus:
    
    ``event.cmd``
        The command name which was matched for this command
    ``event.registry``
        The command registry this command is registered with
``*args``
    A list of values of unnamed groups in the ``args`` regex
``**kwargs``
    A dict of values of named groups in the ``args`` regex

If a keyword argument's value is None, it will not be passed to the function.


.. _contrib_commands_handlers:

Using event handlers as command functions
-----------------------------------------

Instead of registering a command function you can register an instance of
:ref:`class_events_handler`. The handler methods in the command will be passed
the same arguments as :ref:`contrib_commands_functions`. An event handler class
can also use the ``@define_command`` decorator.

For example::

    @define_command(args=r'^(?:at\s+)?(?P<thing>.*)?$', group='room'):
    class ContrivedLookHandler(events.Handler)
        def handler_user(self, event, thing=None):
            event.client.write('You look at the %s' % thing or 'void')
        def handler_others(self, event, thing=None):
            event.service.write_all(
                '%s looks at something' % event.user.name,
                exclude=event.client,
            )
    
    commands.register('look', ContrivedLookHandler())

This is a contrived example, but in practice it means that complex commands
can be split into multiple methods, and inherited from and overridden.


.. _contrib_commands_aliases:

Command aliases
---------------

It's often useful to create command aliases; eg ``'hi`` short for ``say hi``,
or ``n`` short for ``north``. The command registry has built-in support for
alises using the ``alias(match, replace)`` method; for example::

    commands.alias(r'^s$', 'south')
    commands.alias(r'^;', 'emote ')
    commands.alias(r'^!(\S+?) (.*)$', r'emote shouts at \1: \2')

Matches will be evaluated in order they are defined, before commands are
checked.
        
The ``replace`` argument can include backreferences; the arguments will be used
with ``re.sub``, equivalent to::

    input = re.sub(match, replace, input)
 

Subclassing the ``CommandRegistry``
-----------------------------------

By default ``CommandRegistry.parse`` splits received data into command and data
on the first space. This is the basis of a command syntax for talkers and muds.

You can change this behaviour by subclassing the registry and implementing your
own ``parse`` method. It receives the ``Receive`` event, and should return a
tuple of ``(command_name, command_raw_args)``, or raise a ``ValueError`` if the
command is not found or not available.


.. _module_contrib_commands_socials:

``mara.contrib.commands.socials``
=================================

Social commands. These require a :ref:`user store <module_contrib_users>`, and
work best if the user store has the :ref:`gender <module_contrib_users_gender>`
extension on the ``.gender`` attribute.

To add the default socials, call ``gen_social_cmds`` with the service,
commands handler and user store::

    gen_social_cmds(commands)

If defines a social command for each verb in ``SOCIAL_VERBS`` from
:ref:`module_contrib_language``. You can override this by passing a new list
in as ``verbs=['jump', 'run']``.

Behind the scenes each social command is created as an instance of the
``SocialCommand`` class. This can be overridden (eg to change command group or
container) by passing in a subclass as ``command_cls=SocialCommand``.

This module also uses :ref:`module_contrib_language`` to perform basic natural
language processing, to conjugate verbs and convert usernames and pronouns. You
can override the default processor by passing a subclass of ``DirectedAction``
in as ``parser=DirectedAction``.



.. _module_contrib_users:

``mara.contrib.users``
======================

User account management.

Create a user store by subclassing ``BaseUser``::

    from mara.contrib.users import BaseUser
    class User(BaseUser):
        service = service

Add the client's related ``user`` to ``Client`` events by binding
``event_add_user``. This must be done before any other event handlers for
``Client`` events::

    from mara import events
    from mara.contrib.users import event_add_user
    service.listen(events.Client, event_add_user)

There is also an event handler to ask for a user's name when they connect; this
should be used in conjunction with a ``SessionStore``-based user store (for
saved users use the authenticating ``ConnectHandler`` in
:ref:`module_contrib_users_password`)::
    
    from mara.contrib.users import ConnectHandler
    service.listen(events.Connect, ConnectHandler(User))

There are a standard of commands available:

    ``cmd_say`` (eg ``say <message>``)
        Say something to the other users
    ``cmd_emote`` (eg ``emote <message>``)
        Emote something to the other users
    ``cmd_tell`` (eg ``tell <user> <message>``)
        Tell one or more users something
    ``cmd_look`` (eg ``look``)
        Look around (see who is here)
    ``cmd_list_active_users`` (eg ``who``)
        List active users and their idle times
    ``cmd_list_all_users`` (eg ``users``)
        List all online and offline users

These can be registered individually, eg::

    from mara.contrib.users import cmd_look
    commands.register('look', cmd_look)

Or they can be registered in bulk using default command names (see command
examples above)::

    from mara.contrib.users import register_cmds
    register_cmds(commands)

There are also a function to define common aliases; ``'msg`` to ``say msg``,
``;msg`` to ``emote msg`` and ``>who msg`` to ``tell who msg``::

    from mara.contrib.users import register_aliases
    register_aliases(commands)


.. _module_contrib_users_password:

``mara.contrib.users.password``
===============================

Store passwords using salted bcrypt.

Requires the ``bcrypt`` module::

    pip install bcrypt

Add the password mixin to your user store::

    from mara.contrib.users.password import PasswordMixin
    class User(PasswordMixin, BaseUser):
        service = service

This adds a new encrypted ``password`` field to the user store, and two new
methods:

``set_password(pass)``
    Encrypt the password and store it on the object
``check_password(pass)``
    Check the password against the one stored

There is also an event handler to authenticate existing users, or create
accounts for new users::
    
    from mara.contrib.users.password import ConnectHandler
    service.listen(events.Connect, ConnectHandler(User))

There is also an event handler which changes the user's password; use this with
the commands framework::

    from mara.contrib.users.password import ChangePasswordHandler
    commands.register('password', ChangePasswordHandler())


.. _module_contrib_users_admin:

``mara.contrib.users.admin``
============================

Mark users as admins. This will normally be used in conjunction with the
:ref:`passwords <module_contrib_users_password>` user extension.

Add the admin mixin to your user store::

    from mara.contrib.users.gender import AdminMixin
    class User(AdminMixin, BaseUser):
        service = service

There is a command availability helper, ``if_admin``, which can be used with
the ``can`` command definition attribute::

    commands.register('restart', cmd_restart, can=if_admin)

There are two commands available:

    ``cmd_list_admin`` (eg ``admin``)
        List admin users
    ``cmd_set_admin`` (eg ``set_admin bob on``)
        Set or unset admin users

These can either be registered individually, eg::

    from mara.contrib.users.admin import cmd_list_admin
    commands.register('staff', cmd_list_admin)

Or they can be registered in bulk using default command names (see command
examples above)::

    from mara.contrib.users.admin import register_cmds
    register_cmds(commands)


.. _module_contrib_users_gender:

``mara.contrib.users.gender``
=============================

Store a user's gender, to generate accurate pronouns.

Add the gender mixin to your user store::

    from mara.contrib.users.gender import GenderMixin
    class User(GenderMixin, BaseUser):
        service = service

This adds a new ``gender`` field to the user store, which returns a ``Gender``
object with the following attributes:

``type``
    A string set to one of ``'male'``, ``'female'`` or ``'other'``.
    These are available as constants on the class, as
    ``MALE``, ``FEMALE`` and ``OTHER``. Default is ``OTHER``.
    
``subject``
    Pronoun for the subject (he, she or they)
    
``object``
    Pronoun for the object (him, her, they)
    
``possessive``
    Possessive pronoun (his, her, their)
    
``self``
    Referring to oneself (himself, herself, themselves)

There is also a command to check or set gender::

    from mara.contrib.users.gender import cmd_gender
    commands.register('gender', cmd_gender)


.. _module_contrib_language:

``mara.contrib.language``
=========================

Provide natural language processing utils for processing and manipulating
English sentences.

This is an area which has room for improvement.
Natural language processing is a complex topic, and this isn't a comprehensive
solution - stupid things are almost certain to happen. When something does,
please let me know (tweet `@radiac <https://twitter.com/radiac>`_ or add a bug
to github), or better yet, :doc:`contribute a test or fix <../contributing>`.

This is used by :ref:`module_contrib_commands_socials` to modify social actions.


.. _module_contrib_rooms:

``mara.contrib.rooms``
======================

Rooms for users

Create a room store by subclassing ``BaseRoom``::

    from mara.contrib.rooms import BaseRoom
    class Room(BaseRoom):
        service=service

Add a ``room`` attribute and ``move(direction)`` method to your user store with
the ``RoomUserMixin``::

    from mara.contrib.rooms import RoomUserMixin
    class User(RoomUserMixin, PasswordMixin, BaseUser):
        service = service

Create rooms by defining instances of the room store (see
:ref:`contrib_rooms_define` for more details)::

    room_lobby = Room(
        'lobby',
        name='Lobby',
        short='in the lobby',
        desc="You are standing in the lobby",
    )

Add the ``RoomConnectHandler`` mixin to your connect handler to so new users
go into the ``default_room``, and existing users return to the room they were
last in (or the default room if their room has been removed)::

    from mara.contrib.rooms import RoomConnectHandler
    class MudConnectHandler(RoomConnectHandler, ConnectHandler):
        msg_welcome_initial = 'Welcome to the Mara example mud!'
        default_room = room_lobby
    service.listen(events.Connect, MudConnectHandler(User))

Use ``room_restart_handler_factory`` to create a ``PostRestart`` handler, to
put users somewhere if you remove the room they were in::

    from mara.contrib.rooms import room_restart_handler_factory
    service.listen(
        events.PostRestart, room_restart_handler_factory(User, room_lobby)
    )

There are also a set of commands for using the rooms:

    ``cmd_say``, ``cmd_emote``, ``cmd_tell``, ``cmd_look``,
    ``cmd_list_active_users``, ``cmd_list_all_users``
        Room-aware versions of the standard :ref:`module_contrib_users`
        commands
    ``cmd_exits`` (eg ``exits``)
        List available exits
    ``cmd_where`` (eg ``where [<user>]``)
        Show where you are (or another user is)
    ``cmd_goto`` (eg ``goto <room_key>``)
        Jump to another room (normally admin only)
    ``cmd_bring`` (eg ``bring <user>``)
        Bring a user to the room (normally admin only)

These can be registered individually, eg::

    from mara.contrib.commands import cmd_commands
    commands.register('commands', cmd_commands)

There is also a function to generate navigational commands; ``gen_nav_cmds``
will add commands to move in standard directions (north, south, up, down etc)::

    from mara.contrib.rooms import gen_nav_cmds
    gen_nav_cmds(service, commands)

Alternatively, all of these (including navigation) can be registered at once
using default command names (see command examples above)::

    from mara.contrib.rooms import register_cmds
    register_cmds(commands)
    # Or if you are using mara.contrib.users.admin:
    register_cmds(commands, admin=True)

There are also a function to define common aliases; it will add the standard
communication aliases from :ref:`module_contrib_users`, as well as ``l`` to
``look``, and ``n``, ``s``, ``e``, ``w``, ``ne``, ``nw``, ``se``, ``sw`` for
moving in the cardinal directions::

    from mara.contrib.rooms import register_aliases
    register_aliases(commands)


.. _contrib_rooms_define:

Defining rooms
--------------

Rooms can be defined in code as instances of your ``Room`` store. See
:ref:`class_contrib_rooms_baseroom` for details. Rooms are linked to each other
by instances of :ref:`class_contrib_rooms_exit`, managed by the
:ref:`class_contrib_rooms_exits` class.

For example::

    from mara.contrib.rooms import BaseRoom, Exits
    class Room(BaseRoom):
        service=service

    room_lobby = Room(
        'lobby',
        name='Lobby',
        desc='You are in the lobby.',
        exits=Exits(north='pool', south='road'),
    )
    

Rooms can also be defined in YAML, using the YAML instantiator. To load your
YAML rooms::

    from mara.storage import yaml
    yaml.instantiate(service, '/path/to/rooms.yaml')

See :source:`examples/mud/rooms.py` for how to safely use relative paths when
specifying the YAML file to load.

The YAML room definition would look like this::

    store:  room
    key:    lobby
    name:   Lobby
    desc:   You are in the lobby.
    exits:
      north:    pool
      south:    road

To define multiple rooms in a single file, separate each store definition with
the YAML document separator, ``---``. See :ref:`storage_yaml_instantiator` for
more details.


.. _contrib_rooms_referencing:

Referencing rooms
-----------------

Room store classes are not like normal stores: subclasses of a concrete
``BaseRoom`` subclass will share the same manager. This means that rooms of
one class can refer to the keys of other room classes, as long as they
share a common concrete room superclass. Take a look at this contrived
example::

    class Room(BaseRoom):
        service = service
    
    class FancyRoom(Room): pass
    class OtherRoom(Room): pass
    
    class ForeignRoom(BaseRoom):
        service = service
    
    # Instances of the related room classes can refer to each other by key
    r1 = Room('room1', exits=Exits(north='room2'))
    r2 = FancyRoom('room2', exits=Exits(south='room1', north='room3'))
    r3 = OtherRoom('room3', exits=Exits(south='room2'))
    
    # This room can't refer to r1, r2 or r3, so this will fail:
    r4 = ForeignRoom('room4', exits=Exits(north='room1'))
    
    # unless we define a room1 in that set of rooms:
    r5 = ForeignRoom('room1', exits=Exits(south='room4'))
    # Because r1 and r5 don't share a concrete base store class, they both
    # exist independently, despite having the same keys.


.. _class_contrib_rooms_baseroom:

``mara.contrib.rooms.BaseRoom``
-------------------------------


``__init__(...)``

Define a room in code by instantiating your ``Room`` store object with the 
following arguments:

key
    Internal name of room. Must be unique; used by ``Exit`` definitions to
    refer to rooms which have not yet been defined.
    
    Keys are stored between room subclasses which share a concrete ancestor -
    see :ref:`contrib_rooms_referencing` for details.

name
    Name of room, used for titles and describing exits.
    
    Default: ``None``

short
    Short description, used to describe the user's position in the room. This
    will be used after "You are" or "User is".
    
    Default: ``'in the ' + name``

intro
    Introductory block of text; shown on entry to the room, but not when the
    user looks around.
    
    This can either be a single line as a string, or multiple lines as a list
    of strings.
    
    Default: ``None``

desc
    Full room description, shown on entry (after ``intro``) and when the user
    looks around.
    
    This can either be a single line as a string, or multiple lines as a list
    of strings.
    
    Default: ``None``

exits
    Instance of the :ref:`class_contrib_rooms_exits` class, holding the list of
    exit definitions.
    
    Default: ``None``


.. _method_contrib_rooms_room_exit:

``enter(user, exit=None)``
~~~~~~~~~~~~~~~~~~~~~~~~~~

Move the specified ``user`` into the room, show them the intro and description,
and tell others in the room they have arrived.

This will also save the user's profile, so their room is remembered next time
they connect.

If the room was defined with ``clone=True``, this will create a temporary copy
and put the user in there on their own.

If ``exit`` is provided, that is the exit that the user is using; this will be
used to tell others in the room where the user is coming from. If it is not
provided, the user will just appear.


.. _method_contrib_rooms_room_enter:

``exit(user, exit=None)``
~~~~~~~~~~~~~~~~~~~~~~~~~

Remove the specified ``user`` from the room, and tell others in the room they
have left.

If ``exit`` is provided, that is the exit that the user is using; this will be
used to tell others in the room which direction the user is leaving in. If it
is not provided, the user will just disappear.


.. _class_contrib_rooms_exits:

``mara.contrib.rooms.Exits``
----------------------------

An ``Exits`` object is a glorified dict which manages the exits for a room. The
constructor takes the following arguments:

desc
    Static description string for the exits in this room.
    
    If not defined, will be built automatically by
    :ref:`method_contrib_rooms_exits_get_desc`
    
default
    Message to show when a user tries to exit in
    a direction without an exit.
    
    If not set, uses the ``default`` attribute of the class.
    
    To override messages for individual directions, see
    :ref:`class_contrib_rooms_fakeexit`.
    
    Default: ``'You cannot go that way.'``
    
<direction>
    Exit definition
    
    The key must be one of north, south, east, west, northeast, northwest,
    southeast, southwest, up or down.
    
    The value should be an instance of `class_contrib_rooms_exit`, although
    as a shortcut it can be the first value for the ``Exit`` constructor
    (ie the room instance or key)

In addition to the standard ``dict`` methods, the ``Exits`` class has the
following methods:


.. _method_contrib_rooms_exits_get_desc:

``get_desc()``
~~~~~~~~~~~~~~

Used internally to find the description of exits in this room. If ``desc`` was
provided to the constructor that will be returned, otherwise a string
will be built with a list of the defined exits; for example::

    >>> Exits().get_desc()
    'There are no exits'
    
    >>> Exits(south='room1')
    'There is one exit to the south.'
    
    >>> Exits(south='room1', up='room2', east='room3')
    'There are exits to the south, to the east and upwards.'


.. _class_contrib_rooms_exit:

``mara.contrib.rooms.Exit``
---------------------------

An exit holds a reference to the rooms it connects, and manages a user's
movement between rooms.

It has the following attributes and methods:

``__init__(target, related=None)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Define an exit.

Arguments:

    target
        Room that the exit leads to. Can either be a ``Room``
        instance, or the key value for a room that is yet to be
        defined.

    related
        Optional: the related exit is the other side of this exit
        in the target room; for example, if this exit is north, the
        related exit will (usually) be south.


.. _method_contrib_rooms_exit_use:

``use(user)``
~~~~~~~~~~~~~

Make the user use the exit.

It is assumed that they are currently in the ``source`` room. For this reason
you should not normally call this method directly; call
``user.move(direction)`` instead.

It can raise a ``mara.contrib.rooms.ExitError`` if the exit cannot be used
for some reason; the message as defined in ``ExitError(msg)`` will be shown
to the user, and they will stay in their current room. You can use this to
implement exit subclasses with locked doors etc.

If the user can use this exit, it calls the room's
:ref:`enter <method_contrib_rooms_room_enter>` and
:ref:`exit <method_contrib_rooms_room_exit>` methods to move the user and
inform them and others of the move.

``source``
~~~~~~~~~~
The room that has this exit.

``target``
~~~~~~~~~~
The room this exit leads to.

``related``
~~~~~~~~~~~
The related exit is the exit in the target room which leads the user back to
the source room; for example, if this exit is north, the related exit will
(usually) be the south exit in the target room.

If it is not defined, Mara will try to detect it automatically.

``get_desc()``
~~~~~~~~~~~~~~
Return a description of the exit, eg ``'to the south'``.


.. _class_contrib_rooms_fakeexit:

``mara.contrib.rooms.FakeExit``
-------------------------------

Instead of taking a target, it takes a name for the fake exit, and a message to
show a user who tries to use it.

For example::

    Room(
        key='deck', name='the deck of the boat', short='on the deck',
        Exits(
            default="You decide against jumping into the water",
            up=FakeExit('the mast', "Don't be silly, you can't climb the mast")
            down='hold',
        )
    )
