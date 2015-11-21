============
Contributing
============

Contributions are welcome, preferably via pull request. Check the github issues
and project :ref:`roadmap <roadmap>` to see what needs work, but Mara aims to
include as much common generic functionality as is practical - so if you write
something for your service which you think would be a good addition to contrib,
please do send it in.


Installing
==========

The easiest way to work on Mara is to fork the project on github, then install
it to a virtualenv::

    virtualenv mara
    cd mara
    source bin/activate
    pip install -e git+https://github.com/USERNAME/mara.git#egg=mara[full][dev]

(replacing ``USERNAME`` with your username).

This will install the development dependencies too, 

.. _roadmap:

Roadmap
=======
TBC:        * Python 3 support
            * Extend library to support:
              * Multiple rooms
              * Inventory and items
              * Basic combat (health)
            * Support for timers
            * Support for poll, epoll


