from mara.storage.dict import DictStore


async def test_flat_store():
    store = DictStore(a=1, foo="bar")
    data = await store.store()
    assert data == '{"a": 1, "foo": "bar"}'


async def test_flat_restore():
    store = await DictStore.restore('{"a": 1, "foo": "bar"}')
    assert store.a == 1
    assert store.foo == "bar"


async def test_nested_store():
    store = DictStore(a=1, child=DictStore(b=2))
    data = await store.store()
    assert (
        data
        == '{"a": 1, "child": {"_store_class": "DictStore", "data": "{\\"b\\": 2}"}}'
    )


async def test_nested_restore():
    store = await DictStore.restore(
        '{"a": 1, "child": {"_store_class": "DictStore", "data": "{\\"b\\": 2}"}}'
    )
    assert store.a == 1
    assert isinstance(store.child, DictStore)
    assert store.child.b == 2
