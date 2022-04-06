=======
Logging
=======

Mara uses Python's standard ``logging`` framework.

All Mara's loggers are children of ``mara``, and by default the app will filter to show
all ``mara`` log INFO messages upwards.

The log level can be changed by setting the environment variable ``LOGLEVEL``, eg::

    $ LOGLEVEL=DEBUG python echo.py
