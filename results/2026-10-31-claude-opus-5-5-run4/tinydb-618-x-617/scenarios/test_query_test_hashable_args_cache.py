from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage


def between(value, lo, hi):
    return lo <= value <= hi


def test_returned_list_is_fresh_and_write_invalidates():
    db = TinyDB(storage=MemoryStorage)
    db.insert_multiple([{'val': 1}, {'val': 3}, {'val': 9}])

    r1 = db.search(Query().val.test(between, 1, 5))
    assert sorted(d['val'] for d in r1) == [1, 3]
    r1.clear()

    r2 = db.search(Query().val.test(between, 1, 5))
    assert sorted(d['val'] for d in r2) == [1, 3]

    db.insert({'val': 4})
    r3 = db.search(Query().val.test(between, 1, 5))
    assert sorted(d['val'] for d in r3) == [1, 3, 4]


def test_equal_scalar_arg_query_hits_cache():
    db = TinyDB(storage=MemoryStorage)
    db.insert_multiple([{'val': 2}, {'val': 8}])
    table = db.table(db.default_table_name)

    q1 = Query().val.test(between, 0, 5)
    q2 = Query().val.test(between, 0, 5)
    assert q1.is_cacheable()
    assert q1 == q2
    assert hash(q1) == hash(q2)

    assert [d['val'] for d in db.search(q1)] == [2]
    table._read_table = lambda: {}
    assert [d['val'] for d in db.search(q2)] == [2]
