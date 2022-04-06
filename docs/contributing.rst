============
Contributing
============

Contributions are welcome, preferably via pull request. Check the github issues and to
see what needs work.

If you have an idea for a new feature, it's worth opening a new ticket to discuss
whether it's suitable for the project, or would be better as a separate pacakge.


Installing
==========

The easiest way to work on Mara is to fork the project on github, then install it to a
virtualenv::

    virtualenv mara
    cd mara
    source bin/activate
    pip install -e git+git@github.com:USERNAME/mara.git#egg=mara

(replacing ``USERNAME`` with your username).

This will install the testing dependencies too, and you'll find the Mara source ready
for you to work on in the ``src`` folder of your virtualenv.


Testing
=======

It is greatly appreciated when contributions come with tests, and they will lead to a
faster merge and release of your work.

Use ``pytest`` to run the tests::

  cd path/to/mara
  pytest

These will also generate a ``coverage`` HTML report.
