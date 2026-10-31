from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage
from tinydb.operations import add


def test_any_ignores_string_built_by_add_concatenation():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'char': 'a', 'tags': ['a']})
    db.insert({'char': 'b', 'tags': ['z']})

    # Populate the cache before the update so the update must invalidate it
    assert len(db.search(where('tags').any(['a']))) == 1

    db.update(add('char', 'xyz'), where('char') == 'a')
    assert db.get(where('char') == 'axyz') is not None

    # String field must not be treated as a list of characters
    assert db.search(where('char').any(['a', 'x'])) == []
    assert db.count(where('char').any(['x'])) == 0

    # Real list fields still work
    res = db.search(where('tags').any(['a']))
    assert [d['char'] for d in res] == ['axyz']


def test_all_and_get_ignore_string_fields():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'id': 1, 'name': 'ab'})
    db.insert({'id': 2, 'name': ['a', 'b', 'c']})
    db.insert({'id': 3, 'name': ['b', 'a']})

    # get() returns the first match in insertion order; the string doc
    # must be skipped, so the first list doc wins
    doc = db.get(where('name').all(['a', 'b']))
    assert doc is not None
    assert doc['id'] == 2

    assert [d['id'] for d in db.search(where('name').all(['a', 'b']))] == [2, 3]
    assert db.get(where('name').any(['a'])) ['id'] == 2
