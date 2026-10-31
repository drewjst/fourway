from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage


def in_allowed(value, allowed):
    return value in allowed


def _db():
    db = TinyDB(storage=MemoryStorage)
    db.insert_multiple([{'val': 1}, {'val': 2}, {'val': 3}])
    return db


def test_list_arg_query_is_cached_and_equal_query_hits_cache():
    db = _db()
    table = db.table(db.default_table_name)
    q = Query().val.test(in_allowed, [1, 2])
    results = db.search(q)
    assert sorted(d['val'] for d in results) == [1, 2]
    assert q in table._query_cache

    # Bypass storage: an equal, freshly built query must be served from cache
    table._read_table = lambda: {}
    again = db.search(Query().val.test(in_allowed, [1, 2]))
    assert sorted(d['val'] for d in again) == [1, 2]


def test_different_list_args_do_not_collide_in_cache():
    db = _db()
    r1 = db.search(Query().val.test(in_allowed, [1, 2]))
    r2 = db.search(Query().val.test(in_allowed, [3]))
    assert sorted(d['val'] for d in r1) == [1, 2]
    assert [d['val'] for d in r2] == [3]


def test_list_arg_query_cache_invalidated_by_write():
    db = _db()
    q = Query().val.test(in_allowed, [1, 2, 7])
    assert len(db.search(q)) == 2
    db.insert({'val': 7})
    assert sorted(d['val'] for d in db.search(Query().val.test(in_allowed, [1, 2, 7]))) == [1, 2, 7]


def test_nested_dict_in_tuple_arg_and_unhashable_arg_search():
    db = TinyDB(storage=MemoryStorage)
    db.insert_multiple([{'val': 'x'}, {'val': 'y'}])
    table = db.table(db.default_table_name)

    def flag_eq(value, pair):
        return pair[1].get('flag') == value

    res = db.search(Query().val.test(flag_eq, (1, {'flag': 'x'})))
    assert [d['val'] for d in res] == ['x']

    table.clear_cache()

    class Unhashable:
        __hash__ = None

    q = Query().val.test(lambda value, x: True, Unhashable())
    assert not q.is_cacheable()
    assert len(db.search(q)) == 2
    assert len(table._query_cache) == 0


def test_list_arg_cached_results_list_fresh_but_docs_shared():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'val': 1, 'tags': ['a']})

    r1 = db.search(Query().val.test(in_allowed, [1, 2]))
    assert r1 == [{'val': 1, 'tags': ['a']}]
    r1.append({'val': 'junk'})

    r2 = db.search(Query().val.test(in_allowed, [1, 2]))
    assert r2 == [{'val': 1, 'tags': ['a']}]
    assert r2 is not r1

    # Documented behaviour: documents inside are the cached objects
    r2[0]['tags'].append('b')
    r3 = db.search(Query().val.test(in_allowed, [1, 2]))
    assert r3[0]['tags'] == ['a', 'b']
