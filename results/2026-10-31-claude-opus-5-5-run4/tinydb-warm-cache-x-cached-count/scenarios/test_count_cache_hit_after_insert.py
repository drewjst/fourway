from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage


def test_count_uses_cache_and_not_search_after_insert():
    db = TinyDB(storage=MemoryStorage)
    table = db.table('t')
    table.insert({'int': 1})
    table.insert({'int': 2})
    query = where('int') == 1
    assert table.count(query) == 1

    table.insert({'int': 1})
    assert table.count(query) == 2

    calls = []

    def failing_search(cond):
        calls.append(cond)
        raise AssertionError('count() must not call search() on a cache hit')

    table.search = failing_search

    assert table.count(query) == 2
    assert calls == []
