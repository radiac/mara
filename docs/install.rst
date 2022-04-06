============
Installation
============

Installing Mara
===============

Mara requires Python 3.10 or later.

Install to your Python environment with:

.. code-block:: bash

    pip install mara

We recommend using pyenv__ and a virtual environment to manage Mara's Python environment.

.. __: https://github.com/pyenv/pyenv


.. note::

    If you prefer, you can install the development version direct from github instead:


    .. code-block:: bash

        pip install -e git+https://github.com/radiac/mara.git#egg=mara

    This may contain changes made since the last version was released - these will be
    listed in the :doc:`changelog`.

    If you are planning to contribute to Mara, see :doc:`contributing` for more details.


Running the examples
--------------------

The examples are not installed by pip. To try them out, grab them from github:

.. code-block:: bash

    git checkout https://github.com/radiac/mara.git
    cd mara/examples

You can then run the examples using ``python``:

.. code-block:: bash

    python echo.py

All examples listen to 127.0.0.1 on port 9000.


Deploying Mara
==============

If deploying your Mara project to a Linux environment, we recommend using your
distribution's init daemon (eg init.d or systemd) to run your project on boot and
restart it if necessary.

.. TODO: Add instructions for systemd and containerised deployment
