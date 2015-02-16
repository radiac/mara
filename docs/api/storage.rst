.. _storage:

=======
Storage
=======

Cletus provides a storage system which can be used to store data permanently,
or just for the current session. Data is stored in instances of
:ref:`class_store` subclasses, in field attributes defined using
:ref:`class_field` or its subclasses.

Field names cannot start with an underscore, and cannot be one of the store
method names.

Stores should only be accessed using the ``session`` instance, using the
:ref:`method_session_store` method. This ensures data persists across reloads
and restarts.

The ``session`` will instantiated each store with a ``key`` for its associated
data; permanent data for the store is saved in the :ref:`setting_store`
directory, under subfolders for each store class, as json files named by key.

Once you have a ``store`` instance, you can read and write data by accessing
the field attributes.

You can either initialise a ``Field`` with ``save=False`` to make it a
temporary session variable, or set ``_can_save=False`` on your store to make
all of its fields temporary session variables (the ``save`` field argument will
have no power here).


.. _class_store:

``cletus.Store``
================

This is the abstract base class for storage models.

Methods and attributes:

``to_dict()``, ``to_json()``
----------------------------
Serialise store fields to dict or json

Arguments:
:   ``session``:    Optional; if ``True``, include session data, otherwise
                    exclude it. Default: ``False``


``from_dict(dict)``, ``from_json(raw)``
---------------------------------------
Deserialise store fields from dict

Arguments:
:   ``dict`` or ``raw``:    Data to deserialise
    ``session``:    Optional; if ``True``, include session data, otherwise
                    ignore it. Default: ``False``

``save()``
----------
Save permanent data to disk

``load()``
----------
Load permanent data from disk


.. _class_field:

``cletus.Field``
================

Storage variable

``Field()``
-----------

Constructor to create a new field for a Store

Arguments:
:   ``default``:    Optional default value.

                    If it is a callable (eg a function) it will be called each
                    time the store is instantiated, with no arguments. Use this
                    approach for lists and other objects, to avoid references
                    being shared between instances.
                    
                    Default: ``None``
                    
    ``save``:       Optional boolean to state whether or not the field should
                    be saved to disk.
                    
                    This is ignored if ``Store._can_save == False``.
                    
                    Default: ``False``


``init_store(store, name)``
---------------------------

Called by the store when it is initialised. By default this is used to set
the field instance attribute ``name`` on the ``store`` to the default value.
