from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage


def test_count_after_matching_insert_comes_from_kept_cache():
    db = TinyDB(storage=MemoryStorage)
    table = db.table('t')
    table.insert({'int': 1})
    table.insert({'int': 2})
    query = where('int') == 1
    assert table.count(query) == 1

    table.insert({'int': 1, 'x': 'y'})
    table.insert({'int': 3})

    assert query in table._query_cache
    # Any rescan of the table would now see nothing
    table._read_table = lambda: {}
    assert table.count(query) == 2


def test_count_after_non_matching_insert_keeps_cached_value():
    db = TinyDB(storage=MemoryStorage)
    table = db.table('t')
    table.insert({'int': 1})
    query = where('int') == 5
    assert table.count(query) == 0

    table.insert({'int': 1})

    assert query in table._query_cache
    # A rescan would wrongly report one match
    table._read_table = lambda: {'1': {'int': 5}}
    assert table.count(query) == 0
