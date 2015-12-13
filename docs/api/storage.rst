=======
Storage
=======

Mara provides a simple storage system which can be used to store data
permanently, or just for the current session. Data is stored in instances of
:ref:`class_storage_store` subclasses, in field attributes defined using
:ref:`class_storage_field` or its subclasses. Each store is managed by a
:ref:`class_storage_manager`.

Its primary aim is to persist data across restarts; although it can be used for
permanent storage, managers are intentionally simple, and do not provide
functionality for querying or filtering. Data is stored in JSON files, not a
proper database, so for complicated services you should consider using your
Mara stores for session data, with fields holding references to objects from an
ORM such as `SQLAlchemy <http://www.sqlalchemy.org/>`_ or
`Django <https://www.djangoproject.com/>`_.


Overview
========

A store class is defined with the ``session`` instance it is tied to. This
allows the the store to determine its path from settings, and ensures data
persists across restarts. The session identifies it by its class name, which
is also used to contain the store's permanent data in the storage folder.

Each stored object has a unique key - for example, a store for users may use
the username as the key. This is used to load saved data. Store keys will be
converted to lowercase, and can only contain alphabetic characters, digits and
underscore or dash.

Permanent data for the store is saved in the :ref:`setting_store`
directory; each store class has its own subfolders, and each key has its own
file, with data stored in json format.  If you don't want to be able to save a
store, use the :ref:`class_storage_sessionstore` base class when defining it.

Each store has one or more fields to hold data; once you have a ``store``
instance, you can get and set data by accessing the field attributes. You can
define a field with ``session=True`` to make it a temporary session variable.
A plain :ref:`class_storage_field` stores any variable and does not attempt to
do any type coercion - just make sure it can be serialised to JSON if it's a
permanent field. Custom fields can be written to serialise and deserialise more
complex data. Field names cannot start with an underscore, and cannot be one of
the reserved store names (the attributes and methods listed below).

Example
-------

A simple User store (although you don't need to write one of these yourself -
see :ref:`module_contrib_users` for a fully-featured implementation).

Define a store class::

    from mara import storage
    class User(storage.Store):
        # Define class with the session instance it is tied to
        service = service
        
        # Add a couple of fields to be saved
        name = storage.Field()
        desc = storage.Field(default='A poorly-defined blob')
        
        # Add a session field which will only be held in memory
        client = storage.Field(session=True)
        
        # Add some helpful methods for this storage class
        def write(self, *msg):
        

Use the store you have defined to create a store instance::

    # Every store instance needs a key, and you can also pass in field values
    user = User(key=name, name=name)
    
    # Set field values directly on the object
    user.client = event.client
    
    # Save the object to disk
    user.save()

Get stores::
    
    # Active stores (the ones held in memory)
    active_users = User.manager.active()
    
    # Saved stores (the ones only on disk, excluding ones in memory)
    offline_users = User.manager.saved()
    
    # All stores (in memory and on disk)
    all_users = User.manager.all()

Look up a particular user by key::

    # If you only want them if they're active:
    # Returns None if not found
    user = User.manager.get('bob')
    
    # Get them from active or disk
    # Returns None if not found
    user = User.manager.load('bob')


.. _storage_yaml_instantiator:

YAML instantiator
=================

You can instantiate storage objects using YAML to define the keyword arguments
for the constructor. This can be used as an alternative way to provide defaults
for fields, but is more useful if your constructor takes additional keyword
arguments - particularly for objects which have text-heavy hard-coded values,
or if you want to allow people to define store items without giving them access
to the code. For example, this can be used for room or item descriptions
(see :ref:`contrib_rooms_define` for how the ``rooms`` contrib module uses
this).

It requires PyYAML::

    pip install pyyaml

To use the Mara YAML instantiator, pass it the service that the stores are
bound to, and the path to the YAML file::

    from mara.storage import yaml
    yaml.instantiate(service, '/path/to/rooms.yaml')

You will normally call this from your code as it is instantiating, before you
call ``service.run()``. If you want to use a relative path (using the
:ref:`setting_root_path` setting), you will need to run the instantiator after
the ``PreStart`` event once settings have been collected - see
:source:`examples/mud/rooms.py` for an example.

A YAML file can contain multiple documents, separated by ``---``; the Mara YAML
instantiator expects each document to be a store object, so must provide at
least:

    ``store``
        The internal store class name, usually the class name in lowercase -
        see  :ref:`attr_storage_store_name` for more details
    
    ``key``
        The key for the object

It can also take any keyword arguments for the constructor, ie fields, or any
custom keyword arguments your ``__init__()`` method accepts.


See the
`PyYAML documentation <http://pyyaml.org/wiki/PyYAMLDocumentation#YAMLsyntax>`_
for more information about supported YAML syntax.


Example
-------

An example storage class::
    
    class Room(storage.store):
        service = service
        
        # Non-field values
        name = None
        desc = None
        
        # Saved field with room-specific defaults
        items = storage.Field()
    
        def __init__(self, key, name, desc, items, **kwargs):
            super(Room, self).__init__(key, **kwargs)
            self.name = name
            self.desc = desc
            self.items = items

Defining a store in code::

    lobby = Room(
        key='lobby',
        name='Lobby',
        desc='You are in the lobby.',
        items=['cat', 'table', 'plant'],
    )

Defining the same store in a YAML file::

    store:  room
    key:    lobby
    name:   Lobby
    desc:   You are in the lobby.
    items:
    - cat
    - table
    - plant


Storage classes
===============

.. _class_storage_store:

``mara.storage.Store``
----------------------

This is the abstract base class for storage models.

Methods and attributes:

``service``
~~~~~~~~~~~
This must be set to the service responsible for this storage class.

Abstract classes do not need a ``service``.

.. _attr_storage_store_name:

``_name``
~~~~~~~~~
The internal name of the store, used as the directory name for saved stores,
and used as the key to look up a store in the ``service.stores`` dict.

This will normally be set automatically by converting the class name to
lowercase and stripping all characters which aren't a-z, 0-9 or underscore
(``_``) - eg the internal name for a class named ``User`` is ``user``.

Alternatively you can set this variable yourself to force a different internal
name.


``abstract``
~~~~~~~~~~~~
If true, this class will not be registered for use.


``manager``
~~~~~~~~~~~
The :ref:`class_storage_manager` for this store, to provide a way to access
all stored objects.


``to_dict()``, ``to_json()``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Serialise store fields to dict or json

Arguments:
    ``session``
        Optional; if ``True``, include session data, otherwise exclude it.
        
        Default: ``False``


``from_dict(dict)``, ``from_json(raw)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Deserialise store fields from dict

Arguments:
    ``dict`` or ``raw``
        Data to deserialise
    
    ``session``
        Optional; if ``True``, include session data, otherwise ignore it.
        
        Default: ``False``

``save()``
~~~~~~~~~~
Save permanent data to disk

``load()``
~~~~~~~~~~
Load permanent data from disk


.. _class_storage_sessionstore:

``mara.storage.SessionStore``
-----------------------------

This can be used as a base class for session-only stores. It is a subclass of
:ref:`class_storage_store` which disables saving and loading.


.. _class_storage_field:

``mara.storage.Field``
----------------------

Storage variable

``Field()``
~~~~~~~~~~~

Constructor to create a new field for a Store

Arguments:
    ``default``
        Optional default value.

        If it is a callable (eg a function) it will be called each
        time the store is instantiated, with no arguments. Use this
        approach for lists and other objects, to avoid references
        being shared between instances.
        
        Default: ``None``
                    
    ``session``
        Optional boolean to state whether the field is a session
        value (``True``), or if it should be saved to disk
        (``False``).
        
        Default: ``False``


``contribute_to_class(store_cls, name)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Initialise the field on a new store class.

This is called by the store when the class is first created. Normally this
does nothing, but it can be used by a subclass to implement more complex
behaviours, such as replacing the attribute for the field with a descriptor to
manage getting and setting the field value.


``contribute_to_instance(store, name)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Initialise the field value on a new store instance.

This is called by the store when a new instance is initialised. This is
normally used to set the default value for the field, by setting the instance
attribute with the field's ``name`` on the ``store``.

This can be overridden by subclasses to implement more complex behaviours, such
as replacing the attribute with a per-instance object.


.. _method_storage_field_get_value:

``get_value(obj, name)``
~~~~~~~~~~~~~~~~~~~~~~~~

Get the value of this field from the object ``obj``, where the field has the
name ``name``. By default this just returns the value of the named attribute.

This is used internally by :ref:`method_storage_field_serialise`; you should
normally just access the attribute directly on the store instance.


.. _method_storage_field_set_value:

``set_value(obj, name)``
~~~~~~~~~~~~~~~~~~~~~~~~

Set the value of this field on the object ``obj``, where the field has the
name ``name``. By default this just sets the value of the named attribute.

This is used internally by :ref:`method_storage_field_deserialise`; you should
normally just access the attribute directly on the store instance.


.. _method_storage_field_serialise:

``serialise(obj, name)``
~~~~~~~~~~~~~~~~~~~~~~~~

Serialise the field value from the specified field name on the object provided.

This uses :ref:`method_storage_field_get_value` to retrieve the value, and
:ref:`method_storage_field_serialise_value` to serialise it.

This is used to prepare data value for serialisation in a dict to send to
another process via the angel, or to save to disk as a JSON string.


.. _method_storage_field_serialise_value:

``serialise_value(data)``
~~~~~~~~~~~~~~~~~~~~~~~~~~

Used by :ref:`method_storage_field_serialise` to serialise the value returned
by :ref:`method_storage_field_get_value`.

The base class serialiser can serialise dicts, lists and references to Store or
Client objects. Everything else will be passed unchanged.

The easiest way to serialise custom objects is to build them as subclasses of
Store, so they will be serialised automaticaly. Where that's not practical,
override this method in your subclass, as well as write a matching
:ref:`method_storage_field_deserialise_value`. Look at how Mara serialises
``Store`` or ``Client`` objects in :source:`mara/storage/fields.py` for an idea
of how you can serialise your objects.


.. _method_storage_field_deserialise:

``deserialise(obj, name, data)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Deserialise the specified serialised data onto the specified object under the
field name provided.

This uses :ref:`method_storage_field_deserialise_value` to deserialise the
value, and :ref:`method_storage_field_set_value` to set it.

This is used for restoring data from :ref:`method_storage_field_serialise`.


.. _method_storage_field_deserialise_value:

``deserialise_value(obj, data)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Used by :ref:`method_storage_field_deserialise` to deserialise the value for
by :ref:`method_storage_field_set_value`.

The base class deserialiser can deserialise anything that the base serialiser
produces; if you write a custom serialiser, you should write a matching
deserialiser too.

When deserialising references to store objects, the object will be retrieved
from cache if it has already been deserialised, or loaded from disk to be
updated with its serialised data later.



.. _class_storage_manager:

``mara.storage.Manager``
------------------------

Manager for stored objects.

If will often be useful to subclass this when writing a custom store; for
example::

    class UserManager(mara.store.Manager):
        def get_by_username(self, name):
            ...
    
    class User(mara.storage.Store):
        ...
        registry = UserManager()

Note that when assigning the manager to the store, you must assign an instance
of the manager class, not the class itself.


``active()``
~~~~~~~~~~~~
Return a dict of all active objects in the store (including unsaved), keyed
using the object's key.

``saved()``
~~~~~~~~~~~
Return a dict of all objects saved in the store, using the object's key as the
dict key.

``all()``
~~~~~~~~~
Return a dict containing of all active and saved objects, keyed using the
object's key. If an object exists in both saved and live, the live object will
be used.

``add_active(obj)``
~~~~~~~~~~~~~~~~~~~
Make the registry aware of an active object. This is called internally whenever
an object is instantiated.

``remove_active(obj)``
~~~~~~~~~~~~~~~~~~~~~~
Remove an object from the active list when it is no longer needed in memory.
For example, when a user logs out you can call ``User.manager.remove(user)``
to remove them from the user manager's cache.

By default objects are not garbage collected from a store's live cache.

``contribute_to_class(store_cls, name)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Initialise the manager on a new store class.

This is called by the store when the class is first created. It normally
creates and assigns a new instance of the manager. If your custom manager's
constructor takes additional arguments, you should override
``__copy__`` to pass these to the new instance.


