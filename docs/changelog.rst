=========
Changelog
=========

Releases which require special upgrade steps will be marked with a link to instructions.

Changes for upcoming releases will be listed without a release date - these
are available by installing the development branch from github (see
:doc:`install` for details).

Changelog
=========

2.0.0, TBC
-----------------

:ref:`Upgrading from earlier versions <upgrade_0-6-3>`.

Features:

* Moved to an asyncio loop
* Added support for multiple servers


Known issues:

* Removed contrib modules - will return as a separate package
* Angel is not implemented yet


0.7.0, Not released
-------------------

Feature:

* Added Protocol to Client

Changes:

* Client no longer supports telnet by default; must be initialised with the
* Styles refactored to support different renderers
* Setting ``client_buffer_size`` is now ``recv_buffer_size`` and
  ``send_buffer_size``
* Flash policy server has been removed


0.6.3, 2018-10-06
-----------------

Feature:

* Added Python 3.6 support


Bugfix

* Corrected packaging


Note: tests are no longer performed for Python 3.2 or 3.3 as they are EOL


0.6.2, 2017-07-25
-----------------

Bugfix:

* Corrected docs
* Corrected manifest


0.6.1, 2016-10-20
-----------------

Bugfix:

* Improved password hashing algorithm (merges #5)
* Fixed empty password handling (merges #6)

Internal:

* Improved support for custom password hashing algorithms, with support for
  passwords stored using old algorithms

Thanks to:

* Marcos Marado (marado) for #5 and #6


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

* Added class-based event handlers, with support for use as command functions
* Added room support
* Added YAML-based store instantiation
* Added command aliases
* Refactored user-related commands from talker example
* Simplified social command definition and generation
* Added styles

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

* Initial release of new version in Python
