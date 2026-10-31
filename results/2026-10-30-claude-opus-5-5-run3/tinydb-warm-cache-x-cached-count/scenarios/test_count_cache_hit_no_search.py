from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage


def test_count_does_not_call_search_on_cache_hit_after_insert():
    db = TinyDB(storage=MemoryStorage)
    table = db.table('t')
    table.insert_multiple([{'int': 1}, {'int': 2}])
    query = where('int') == 1

    table.insert({'int': 1})
    # First count may need to search (cache miss on some trees)
    assert table.count(query) == 2

    calls = []

    def forbidden_search(cond):
        calls.append(cond)
        raise AssertionError('count() must not call search() on a cache hit')

    table.search = forbidden_search

    assert table.count(query) == 2
    assert table.count(query) == 2
    assert calls == []
