==============
cletus.contrib
==============

The ``contrib`` module contains functionality which isn't used by the core of
Cletus, but which can be useful when building your own services.


.. _class_contrib_commands:

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

If a command suffers an exception, it will be logged to the ``command`` log
level, and if ``settings.commands_debug`` is ``True``, it will also be sent
to the client who entered the command.


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
name is known) can have their parameters pre-defined with the
``@define_command`` decorator:

    from cletus.contrib.commands import define_command
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
   
:   args:       Optional regular expression to match arguments
                (case insensitive)
    syntax:     Optional human-readable syntax
    group:      Optional command group
    help:       Optional help; if missing, will be taken from docstring
    can         Optional callback to determine command availability.
                It is passed the event, and if it returns True, the
                command can be used. If not set, it can always be used.
    context:    Optional object to set as CommandEvent.context


Command functions
-----------------

Command functions are passed the following arguments:

:   event:      A ``CommandEvent`` based on the ``Receive`` event, (ie
                containing its ``service``, ``client`` etc), plus:
                
                ``event.cmd``:          The command name which was matched for
                                        this command
                ``event.registry``:     The command registry this command is
                                        registered with
    *args:      A list of values of unnamed groups in the ``args`` regex
    **kwargs    A dict of values of named groups in the ``args`` regex

If a keyword argument's value is None, it will not be passed to the function.


Subclassing the ``CommandRegistry``
-----------------------------------

By default ``CommandRegistry.parse`` splits received data into command and data
on the first space. This is the basis of a command syntax for talkers and muds.

You can change this behaviour by subclassing the registry and implementing your
own ``parse`` method. It receives the ``Receive`` event, and should return a
tuple of ``(command_name, command_raw_args)``, or raise a ``ValueError`` if the
command is not found or not available.


.. _class_contrib_commands_socials:

``cletus.contrib.commands.socials``
===================================

Social commands. These require a :ref:`user store <class_contrib_users>`, and
work best if the user store has the :ref:`gender <class_contrib_users_gender>`
extension on the ``.gender`` attribute.

To add the default socials, call ``gen_social_cmds`` with the service,
commands handler and user store::

    gen_social_cmds(service, commands, User)

This module uses :ref:`class_contrib_language`` to get its list of social verbs
and to perform basic natural language processing to conjugate verbs and convert
usernames and pronouns.


.. _class_contrib_users:

``cletus.contrib.users``
========================

User account management.

Create a user store by subclassing ``BaseUser``::

    from cletus.contrib.users import BaseUser
    class User(BaseUser):
        service = service

Add the client's related ``user`` to ``Client`` events by binding
``event_add_user``. This must be done before any other event handlers for
``Client`` events::

    from cletus import events
    from cletus.contrib.users import event_add_user
    service.listen(events.Client, event_add_user)

Add a client serialiser so that the user object can be restored after a
restart::

    from cletus.contrib.users import BaseUserSerialiser
    class UserSerialiser(BaseUserSerialiser):
        service = service
        store_name = 'user'
        attr = 'user'

Add a command to list all users:

    from cletus.contrib.users import cmd_list_users
    commands.register('users', cmd_list_users, context={'User': User})


.. _class_contrib_users_password:

``cletus.contrib.users.password``
=================================

Store passwords using salted bcrypt.

Requires the ``bcrypt`` module::

    pip install bcrypt

Add the password mixin to your user store:

    from cletus.contrib.users.password import PasswordMixin
    class User(PasswordMixin, BaseUser):
        service = service

This adds a new encrypted ``password`` field to the user store, and two new
methods:

:   set_password(pass):     Encrypt the password and store it on the object
    check_password(pass):   Check the password against the one stored


.. _class_contrib_users_admin:

``cletus.contrib.users.admin``
==============================

Mark users as admins. This will normally be used in conjunction with the
:ref:`passwords <class_contrib_users_password>` user extension.

Add the admin mixin to your user store::

    from cletus.contrib.users.gender import AdminMixin
    class User(AdminMixin, BaseUser):
        service = service

There is a command availability helper, ``if_admin``, which can be used with
the ``can`` command definition attribute::

    commands.register('restart', cmd_restart, can=if_admin)

There are two commands available, one to list admin users, and another to set
or unset admin users::

    from cletus.contrib.users.admin import cmd_list_admin, cmd_set_admin
    commands.register('admin', cmd_list_admin, context={'User': User})
    commands.register(
        'set_admin', cmd_set_admin, context={'User': User}, can=if_admin,
    )

.. _class_contrib_users_gender:

``cletus.contrib.users.gender``
===============================

Store a user's gender, to generate accurate pronouns.

Add the gender mixin to your user store::

    from cletus.contrib.users.gender import GenderMixin
    class User(GenderMixin, BaseUser):
        service = service

This adds a new ``gender`` field to the user store, which returns a ``Gender``
object with the following attributes:

:   type:       A string set to one of ``'male'``, ``'female'`` or ``'other'``.
                These are available as constants on the class, as
                ``MALE``, ``FEMALE`` and ``OTHER``. Default is ``OTHER``.
    subject:    Pronoun for the subject (he, she or they)
    object:     Pronoun for the object (him, her, they)
    possessive: Possessive pronoun (his, her, their)
    self:       Referring to oneself (himself, herself, themselves)

There is also a command to check or set gender:

    from cletus.contrib.users.gender import cmd_gender
    commands.register('gender', cmd_gender)


.. _class_contrib_language:

``cletus.contrib.language``
===========================

Provide natural language processing utils for processing and manipulating
English sentences.

This is an area which has room for improvement.
Natural language processing is a complex topic, and this isn't a comprehensive
solution - stupid things are almost certain to happen. When something does,
please let me know (tweet `@radiac <https://twitter.com/radiac>`_ or add a bug
to github), or better yet, :doc:`contribute a test or fix <../contributing>`.

This is used by :ref:`class_contrib_commands_socials` to modify social actions.


.. _class_contrib_rooms:

``cletus.contrib.rooms``
========================

This provides a ``Room`` store for keeping track of ``User`` objects.

It extends the ``User`` store with a ``room`` field.


