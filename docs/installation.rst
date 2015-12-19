============
Installation
============

Installing Mara
===============

Supports Python 2.7 and 3.2 or later. The only required dependency is ``six``.

Installation is simple with pip::

    pip install mara

or to install with optional dependencies::

    pip install mara[full]

This will install the following additional modules:

* ``dateutil`` for the date-based timer :ref:`class_timers_date_datetimer`
* ``pyyaml`` for the :ref:`YAML store instantiator <storage_yaml_instantiator>`
* ``bcrypt`` for provides encryption in :ref:`module_contrib_users_password`

You can now build and run your service, as described in :doc:`introduction`.

.. note::
    If you prefer, you can instead install the development version direct from
    github::
   
        pip install -e git+https://github.com/radiac/mara.git#egg=mara[full]
    
    This may contain changes made since the last version was released -
    these will be listed in the :ref:`changelog`.
    
    If you are planning to contribute to Mara, you may want to install
    with the ``dev`` extra requirements - see :doc:`contributing` for more
    details.



Running the examples
--------------------

The examples are not installed by pip; to try them out, grab them from github::

    git checkout https://github.com/radiac/mara.git
    cd mara/examples

You can then run the examples using ``python``, or ``mara`` if you want to use
the :ref:`angel`::

    python echo.py
    python chat.py
    mara talker.py
    mara mud.py

All examples listen to 127.0.0.1 on port 9000.


Keeping Mara running
======================

You can run a Mara process by just calling it from your shell, but it will
stop when you log out or reboot your server.

To make sure your Mara process stays running, you should set up your
operating system to run it when your server starts, and to monitor it to keep
it running.

In Ubuntu the easiest way to achieve this is with ``upstart``; add a script to
``/etc/init/myservice`` containing::

    description "Mara server for myservice"
    start on runlevel [2345]
    stop on runlevel [!2345]
    respawn
    exec /usr/bin/python /path/to/myservice

.. note::
    Default settings use paths relative to your service script, so in this
    example the store will be created at ``/path/to/store``. If you do not
    want this, you can either either provide a ``root_path`` setting::
    
        exec /usr/bin/python /path/to/myservice --root_path=/path/to/myservice
    
    or change the settings to use absolute paths::
    
        exec /usr/bin/python /path/to/myservice \
            --store_path=/home/mud/store \
            --angel_socket=/var/run/mud_angel.socket

If your version of upstart supports user jobs it would be best to put it there,
otherwise if it's in ``/etc/init/`` or ``/etc/event.d/`` you will probably want
to change user to avoid running it as root (replace ``ARGS`` with Mara args)::

    exec start-stop-daemon --start --chuid USER \
        --exec /usr/bin/python -- /path/to/myservice ARGS

If you installed into a virtual environment, change the exec path to the
correct version of python::

    exec /path/to/venv/bin/python /path/to/myservice

You may also want to use the angel, so that you can take advantage of seamless
restarts::

    exec /path/to/bin/mara /path/to/myservice

You can then start and stop the process using upstart::

    sudo start myservice
    sudo stop myservice

So, say you want a virtualenv install at ``/home/mud/mara``, with your service
defined in ``/home/mud/code/mud.py``, using the angel, running as the ``mud``
user, using the settings in ``/home/mud/code/mud/settings.py``, but overriding
the root path so all your Mara-created files (logs, store, angel socket etc)
are in ``/home/mud/data``; put the following in your upstart file ``mara_mud``,
which you can then run with ``sudo start mara_mud``::

    description "Mara angel for mud"
    start on runlevel [2345]
    stop on runlevel [!2345]
    respawn
    exec start-stop-daemon --start --chuid mud \
        --exec /home/mud/mara/bin/mara -- \
        /home/mud/code/mud.py module:mud.settings \
        --root_path=/home/mud/data
