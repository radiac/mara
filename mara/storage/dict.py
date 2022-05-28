import json
from typing import Any

from .base import Store, store_classes


class DictStore(Store, dict):
    """
    A dict-based store with no permanence

    For convenience, keys are also available as attributes.

    To freeze a special case value, define:

    * ``freeze_KEY(key:str, value:Any) -> Any`` which must return a value serialisable
      by ``json``, and
    * ``thaw_KEY(key:str, value:Any) -> Any`` which converts the frozen value back into
      the real value

    replacing ``KEY`` with the key of the special case value.
    """

    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value

    async def store(self) -> str:
        # Start by making all values safe to serialise
        safe = {}
        for key, value in self.items():
            safe[key] = await self._freeze_item(key, value)

        # Now serialise to json
        data = json.dumps(safe)
        return data

    async def _freeze_item(self, key: str, value: Store | Any) -> Any:
        """
        Make value safe to serialise
        """
        freezer_fn_name = f"freeze_{key}"
        if freezer_fn_name in dir(self):
            # can't use hasattr/getattr because of __getattr__
            freezer_fn = getattr(self, freezer_fn_name)
            return freezer_fn(key, value)

        elif isinstance(value, Store):
            data = await value.store()
            return {
                "_store_class": type(value).__name__,
                "data": data,
            }

        return value

    @classmethod
    async def restore(cls, data: str):
        """
        Deserialise and create a new object
        """
        # Deserialise from JSON
        safe = json.loads(data)

        # Thaw values
        kwargs = {}
        for key, value in safe.items():
            kwargs[key] = await cls._thaw_item(key, value)

        return cls(**kwargs)

    @classmethod
    async def _thaw_item(cls, key: str, value: Any) -> Any:
        thaw_fn_name = f"freeze_{key}"
        if thaw_fn_name in dir(cls):
            # can't use hasattr/getattr because of __getattr__
            thaw_fn = getattr(cls, thaw_fn_name)
            return thaw_fn(key, value)

        elif isinstance(value, dict) and "_store_class" in value:
            store_cls_name = value["_store_class"]
            store_cls = store_classes[store_cls_name]
            obj = await store_cls.restore(value["data"])
            return obj

        return value
