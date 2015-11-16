.. _storage:

=======
Storage
=======

Cletus provides a simple storage system which can be used to store data
permanently, or just for the current session. Data is stored in instances of
:ref:`class_storage_store` subclasses, in field attributes defined using
:ref:`class_storage_field` or its subclasses. Each store is managed by a
:ref:`class_storage_manager`.

Store keys will be converted to lowercase, and can only contain alphabetic
characters, digits and underscore or dash.

Field names cannot start with an underscore, and cannot be one of the reserved
store names (the attributes and methods listed below).

A store class must be defined with the ``session`` instance it is tied to.
This allows the the store to determine its path from settings, and ensures data
persists across restarts.

Permanent data for the store is saved in the :ref:`setting_store`
directory; each store class has its own subfolders, and each key has its own
file, with data stored in json format.

Once you have a ``store`` instance, you can get and set data by accessing
the field attributes.

You can initialise a ``Field`` with ``session=True`` to make it a temporary
session variable. If you don't want to be able to save a store at all,
use the :ref:`class_tempstoremixin` mixin when defining the class.

Managers are intentionally simple, and do not provide functionality for
querying or filtering; data is stored in JSON files, not a proper database. For
anything complicated you would be better off just using cletus stores for
session data with fields holding references to ORM objects, which can store
permanent data in a more sensible structure than separate JSON files, and far
more appropriate for being queried.


.. _class_storage_store:

``cletus.storage.Store``
========================

This is the abstract base class for storage models.

Methods and attributes:

``service``
-----------
This must be set to the service responsible for this storage class.

Abstract classes do not need a ``service``.

``abstract``
------------
If true, this class will not be registered for use.

``manager``
-----------
The :ref:`class_store_manager` for this store, to provide a way to access
all stored objects.


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
    ``session``:            Optional; if ``True``, include session data,
                            otherwise ignore it. Default: ``False``

``save()``
----------
Save permanent data to disk

``load()``
----------
Load permanent data from disk


.. _class_store_field:

``cletus.storage.Field``
========================

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
                    
    ``session``:    Optional boolean to state whether the field is a session
                    value (``True``), or if it should be saved to disk
                    (``False``).
                    
                    Default: ``False``


``contribute_to_class(store_cls, name)``
----------------------------------------

Initialise the field on a new store class.

This is called by the store when the class is first created. Normally this
does nothing, but it can be used by a subclass to implement more complex
behaviours, such as replacing the attribute for the field with a descriptor to
manage getting and setting the field value.


``contribute_to_instance(store, name)``
---------------------------------------

Initialise the field value on a new store instance.

This is called by the store when a new instance is initialised. This is
normally used to set the default value for the field, by setting the instance
attribute with the field's ``name`` on the ``store``.

This can be overridden by subclasses to implement more complex behaviours, such
as replacing the attribute with a per-instance descriptor, to hold data
internally for that store instance.


.. _method_store_field_serialise:

``serialise(obj, name)``
------------------------

Serialise the field value from the specified field name on the object provided.

This is used for service reloads, and preparing data to be encoded to JSON to
be saved to disk.

When reloading, remember that core cletus object instances will persist
(``Service``, ``Client`` etc), and any objects in your code must be destroyed.
This means that if you set an attribute on a ``service`` or ``client`` instance
which references one of your objects, your code must update these attributes
so that the objects use your new reloaded code, and the old code can be garbage
collected.

for an example, take a look at ``cletus.contrib.users.ClientField``:
* Because the ``User`` store will be destroyed and recreated, but the
  ``Client`` instance will persist, it clears and sets the ``client.user``
  attribute
* Because the ``Client`` instance will persist, it intentionally allows the
  ``client`` value to be serialised as a reference. The ``ClientField`` is
  a session-only field, so this will not cause problems for JSON encoding.



.. _method_store_field_deserialise:

``deserialise(obj, name, data)``
--------------------------------

Deserialise the specified serialised data onto the specified object under the
field name provided.

This is used for service reloads, and restoring data from decoded from JSON
when being loaded from disk.


.. _class_storage_manager:

``cletus.storage.Manager``
==========================

Manager for stored objects.

If will often be useful to subclass this when writing a custom store; for
example::

    class UserManager(cletus.store.Manager):
        def get_by_username(self, name):
            ...
    
    class User(cletus.storage.Store):
        ...
        registry = UserManager()

Note that when assigning the manager to the store, you must assign an instance
of the manager class, not the class itself.


``active()``
------------
Return a dict of all active objects in the store (including unsaved), keyed
using the object's key.

``saved()``
-----------
Return a dict of all objects saved in the store, using the object's key as the
dict key.

``all()``
---------
Return a dict containing of all active and saved objects, keyed using the
object's key. If an object exists in both saved and live, the live object will
be used.

``add_active(obj)``
-------------------
Make the registry aware of an active object. This is called internally whenever
an object is instantiated.

``remove_active(obj)``
----------------------
Remove an object from the active list when it is no longer needed in memory.
For example, when a user logs out you can call ``User.manager.remove(user)``
to remove them from the user manager's cache.

By default objects are not garbage collected from a store's live cache.

``contribute_to_class(store_cls, name)``
----------------------------------------

Initialise the manager on a new store class.

This is called by the store when the class is first created. It normally
creates and assigns a new instance of the manager. If your custom manager's
constructor takes additional arguments, you should override
``__copy__`` to pass these to the new instance.
