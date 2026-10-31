from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage


def test_count_after_insert_served_from_maintained_cache():
    db = TinyDB(storage=MemoryStorage)
    table = db.table('t')
    table.insert({'int': 1})
    match = where('int') == 1
    miss = where('int') == 7
    assert table.count(match) == 1
    assert table.count(miss) == 0

    table.insert({'int': 1, 'char': 'b'})

    assert match in table._query_cache
    assert miss in table._query_cache

    # Storage reads would now yield nothing: the answers must come from
    # the cache that insert() kept up to date.
    table._read_table = lambda: {}

    assert table.count(match) == 2
    assert table.count(miss) == 0
    assert table.search(match) == [{'int': 1}, {'int': 1, 'char': 'b'}]
