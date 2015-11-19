============
Installation
============

Requires Python 2.7 or later

Installation is simple with pip:

    pip install cletus

.. note::
    If you prefer, you can instead install the development version direct from
    github::
   
        pip install -e git+https://github.com/radiac/cletus.git#egg=cletus
    
    This may contain changes made since the last version was released -
    these will be listed in the :ref:`changelog`.

You can now build and your service, as described in :doc:`introduction`.


Keeping Cletus running
======================

You can run a Cletus process by just calling it from your shell, but it will
stop when you log out or reboot your server.

To make sure your Cletus process stays running, you should set up your
operating system to run it when your server starts, and to keep it running.

In Ubuntu the easiest way to achieve this is with ``upstart``; add a script to
``/etc/init/myservice`` containing::

    description "Cletus server for myservice"
    start on runlevel [2345]
    stop on runlevel [!2345]
    respawn
    exec /usr/bin/python /path/to/myservice

If your version of upstart supports user jobs it would be best to put it there,
otherwise if it's in ''/etc/init/'' or ''/etc/event.d/'' you will probably want
to change user to avoid running it as root (replace ARGS with cletus args)::

    exec start-stop-daemon --start --chuid USER --exec /usr/bin/python -- /path/to/myservice ARGS

If you installed into a virtual environment, change the exec path to the
correct version of python::

    exec /path/to/venv/bin/python /path/to/myservice

You may also want to use the angel, so that you can take advantage of seamless
restarts::

    exec /path/to/bin/cletus /path/to/myservice

You can then start and stop the process using upstart:
    sudo start myservice
    sudo stop myservice
