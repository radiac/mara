=========
Upgrading
=========

For an overview of what has changed between versions, see the :ref:`changelog`.
For instructions for upgrading from a specific version, see
:ref:`instructions`.


.. _changelog:

Changelog
=========

0.7.0, in progress
------------------

Feature:

* Added contrib items and item containers
* Event listeners can now be defined with ``front=True`` to add them to the
  front of the event stack, rather than to the end.
* Handler instances have an ``.extend(mixin)`` method to make reusable handlers
  and mixins easier to work with
* Command registry has a matching `.extend(cmd, mixin)` command
* Standard commands are now all Handler-based
* Added ``KeylessStore``, for session objects without keys.

  These will not be serialised by their managers (managers store no cache), but instead they are serialised in-place when found ona fied, eg items - each
  Sword instance may have its own attributes, but they will not have unique
  keys, and do not need to be persisted individually.
* When using rooms, client events ``container`` attribute will now always point
  at the user's room

Internal:

* Moved ``container`` attribute from ``Handler`` instances onto the ``event``
* Changed service.events to a deque
* Removed ``contrib.rooms.commands.RoomHandler`` in favour of the ``Client``
  event handler ``contrib.rooms.user.event_add_room_container``
* Removed user-related commands from ``contrib.rooms``, added a ``LookMixin``
* ``Field.deserialise`` now has a 5th compulsory argument, the ``session`` flag

Bugfixes:

* Corrected manifest
* Pinned travis virtualenv to maintain Python 3.2 support


0.6.0, 2015-12-20
-----------------

Feature:

* Python 3 support (3.2, 3.3, 3.4 and 3.5)
* Unicode support

Changed:

* Changed ``write`` to accept ``newline=False`` kwarg, to control whether the
  line ends with a newline when the socket is not in raw mode
* Example echo service now runs in raw mode
* The command registry can now unregister commands

Internal:

* Added angel.stop() to terminate angel from threads
* Fixed angel's start delay reset when starting a service without a saved state


0.5.0, 2015-12-13
-----------------

Feature:

* Added class-based event handlers, with support for use as command functions -
  see :ref:`class_events_handler`
* Added room support - see :ref:`module_contrib_rooms`
* Added YAML-based store instantiation - see :ref:`storage_yaml_instantiator`
* Added command aliases - see :ref:`contrib_commands_aliases`
* Refactored user-related commands from talker example into
  :source:`mara/contrib/users/commands.py`
* Simplified social command definition and generation - see
  :ref:`module_contrib_commands_socials`
* Added :ref:`module_styles`

Removed:

* Replaced ClientSerialiser with improved Field serialiser
* Replaced StoreField with improved Field serialiser
* Removed socials import from contrib.commands, so the code is now only loaded
  if you specifically want it

Internal:

* Added client containers
* Added ``active`` to the list of reserved store field names
* Changed test root dir to ``examples``


0.4.0, 2015-11-21
-----------------

Feature:

* Renamed project
* Added angel to support seamless restarts

Internal:

* Added root_path setting for more reliable relative paths


0.3.0, 2015-02-16
-----------------

Feature:

* Restructured from plugin-based command to framework


0.2.1, 2012-01-20
-----------------

Feature:

* Extra commands in plugins

Internal:

* Better command error handling - now piped to users
* Plugins now private namespaces with shared dict 'publics'


0.2.0, 2012-01-18
-----------------

Feature:

* Added telnet negotiation
* Added socials

Internal:

* Added support for different newline types
* Split User into User and Client objects
* Added argument parsing to Command object


0.1.1, 2012-01-16
-----------------

Internal:

* Rearranged plugin files to improve clarity
* Internal: Plugin lists


0.1.0, 2012-01-15
-----------------

Feature:

* Events, plugins
* IRC- and MUD-style chat

Internal:

* Moved all non-core code into plugins


0.0.1, 2012-01-13
-----------------

Feature:

* Initial release of new version in python


.. _instructions:

Instructions
============

1. Check which version of Mara you are upgrading from::

    python -c "import mara; print mara.__version__"

2. Upgrade the Mara package::

    pip install mara --upgrade

3. Upgrade your code following the upgrade instructions below for **all**
   appropriate versions.


Upgrading from 0.6.0
--------------------

``event.container``
~~~~~~~~~~~~~~~~~~~

The ``handler.container`` has been removed, and ``event.container`` added in
its place.

Any ``handler_`` methods in your event handler classes which previously
referred to ``self.container`` should now use ``event.container`` instead.


Room command handler
~~~~~~~~~~~~~~~~~~~~

The base command handler ``contrib.rooms.commands.RoomHandler`` has been removed
and replaced with a ``Client`` event handler
``contrib.rooms.user.event_add_room_container``. This should be added to your
``Client`` listeners immediately after ``event_add_user``::

    service.listen(events.Client, event_add_user)
    service.listen(events.Client, event_add_room_container)


Room commands
~~~~~~~~~~~~~

User-related commands have been removed from ``contrib.rooms``, and should now
be imported from ``contrib.users`` instead.

If previously you called ``contrib.rooms.register_cmds``, you must now call
``contrib.users.register_cmds`` first::

    from mara.contrib.users import register_cmds as users_register_cmds
    from mara.contrib.rooms import register_cmds as rooms_register_cmds

    users_register_cmds(commands)
    rooms_register_cmds(commands, admin=True)

If instead you imported and defined commands from ``rooms`` individually, you
must now import then from ``users``. There is a new ``LookMixin``, which should
be used to extend ``users.cmd_look``:

    commands.register('look', contrib.users.cmd_look)
    commands.extend('look', contrib.rooms.LookMixin)


Storage
~~~~~~~

Mara 0.7.0 changes the arguments for ``storage.Field.deserialise``. If any of
your field subclasses have a custom ``deserialise`` method, they must now
take a 5th argument ``session``.


Upgrading from 0.5.0
--------------------

Mara 0.6.0 now supports unicode when calling ``write`` and ``write_all`` on a
client or container, or when receiving data. The ``client.write_raw`` method
only supports bytestrings, so should not be used for suppressing the newline
character; instead pass the ``newline`` keyword argument to ``write``
(supported by client, container and user classes)::

    client.write('Enter something: ', newline=False)

There should not be any other changes required for unicode support; the client
manages convertion between byte strings and utf-8, and the ``write`` methods
support either. Received data in Receive events are now unicode strings.

Unicode support does not affect services operating with
:ref:`setting_socket_raw` set to ``True``.

The angel now waits until after a new service has called ``PostStart`` and
``PostRestart`` before terminating the old service, so anything which needs to
be cleaned (eg open filehandles) before that happens should take place in
``PreRestart``.


Upgrading from 0.4.0
--------------------

The class ``mara.service.Service`` now inherits from
``container.ClientContainer``, which means the ``get_all`` attribute has been
renamed to ``filter_clients``.

The class ``mara.storage.StoreField`` has been removed; replace your use of it
with the normal ``mara.storage.Field``, which can now automatically serialise
and deserialise references to ``Store`` instances. The field now also supports
the use of store instances in list and dict values.

Client serialisers have been removed; you should now write custom fields with
their own ``serialise`` and ``deserialise`` methods, which can then set
attributes on the client object; see ``ClientField`` in
:source:`mara/contrib/useres/base.py` for an example.

The module ``mara.contrib.commands.socials`` is no longer imported into
``mara.contrib.commands``, so change your imports to specify the ``socials``
module.

The command function ``mara.contrib.users.cmd_list_users`` has been renamed to
``cmd_list_all_users``. That command and the two admin commands,
``cmd_list_admin`` and ``cmd_set_admin``, no longer need the ``User`` context.

The talker example now uses the command registry's built-in aliases feature
instead of defining a custom command - see
:ref:`contrib_commands_aliases`, :source:`mara/contrib/users/commands.py` and
:source:`examples/talker/commands.py`.

The social command generator takes different arguments; for normal usage it
now only needs the command registry, eg ``gen_social_cmds(commands)``.

The undocumented colour functions and ``HR`` have been removed from ``util`` in
favour of the new :ref:`module_styles` classes.

``Store`` classes now cannot have fields named ``active`` - it is now a
reserved word. If you have a field with this name, you will need to rename it.
