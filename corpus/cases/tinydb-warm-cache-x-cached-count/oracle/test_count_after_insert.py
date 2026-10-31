from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage


def test_a_cached_count_sees_a_later_insert():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'int': 1})
    query = where('int') == 1
    assert db.count(query) == 1

    db.insert({'int': 1})

    assert db.count(query) == 2
