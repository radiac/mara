store_classes = {}


class Store:
    """
    A class which can store and restore its data

    Each Store subclass is responsible for how it stores and restores itself using a
    single string value; for example, the DictStore serialises to json which is
    returned raw, while the SqliteStore saves data to an sqlite database and returns the
    database ID of the object.

    Each Store subclass must have a unique name, as it uses that to register itself with
    the global store class registry, so that store class names mentioned in serialised
    data can be restored.

    A subclass must implement store() and restore()

    Abstract subclasses should set abstract=True in their definition, eg::

        class MyAbstractStore(Store, abstract=True):
            ...
    """

    def __init_subclass__(cls, *, abstract=False, **kwargs):
        super().__init_subclass__(**kwargs)
        if not abstract:
            store_classes[cls.__name__] = cls

    async def store(self) -> str:
        raise NotImplementedError()

    @classmethod
    async def restore(cls, data: str) -> None:
        raise NotImplementedError()
