from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage
from tinydb.operations import subtract


def test_plain_query_evaluation_and_caching():
    q = where('int') == 1
    assert q({'int': 1}) is True
    assert q({'int': 2}) is False
    assert q({'nested': {'int': 1}}) is False
    nested = where('a').b == 3
    assert nested({'a': {'b': 3}})
    assert not nested({'a': 3})

    db = TinyDB(storage=MemoryStorage)
    db.insert_multiple({'int': 1, 'char': c} for c in 'abc')
    combined = (where('int') == 1) & ~(where('char') == 'b')
    assert db.count(combined) == 2
    assert combined in db._query_cache
    assert db.count(q) == 3
    assert q in db._query_cache


def test_subtract_operation_and_cache_invalidation():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'int': 1, 'char': 'a'})
    q = where('int') == -4
    assert db.count(q) == 0
    db.update(subtract('int', 5), where('char') == 'a')
    assert db.get(where('char') == 'a')['int'] == -4
    assert db.count(q) == 1
