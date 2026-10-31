from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage


def test_query_repr_stable():
    q = where('a') == 1
    assert repr(q) == "QueryImpl('==', ('a',), 1)"
    assert repr(~q) == "QueryImpl('not', ('==', ('a',), 1))"


def test_query_cache_visible_after_update():
    db = TinyDB(storage=MemoryStorage)
    db.insert_multiple({'int': 1, 'char': c} for c in 'abc')
    q = where('int') == 1
    assert db.count(q) == 3
    assert q in db._query_cache
    db.update({'int': 2}, doc_ids=[1])
    assert q not in db._query_cache
    assert db.count(q) == 2
    assert db.tables() == set(['_default'])
