from tinydb import TinyDB, where, Query
from tinydb.storages import MemoryStorage


def test_get_first_match_with_list_any_all():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'id': 1, 'tags': ['x', 'y']})
    db.insert({'id': 2, 'tags': ['x']})
    db.insert({'id': 3, 'tags': [{'n': 'x'}]})

    assert db.get(where('tags').any(['x']))['id'] == 1
    assert db.get(where('tags').all(['x']))['id'] == 1
    assert db.get(where('tags').any(Query().n == 'x'))['id'] == 3
    assert [d['id'] for d in db.search(where('tags').any(['x']))] == [1, 2]

    # Update must become visible through a previously cached query
    db.update({'tags': ['q']}, doc_ids=[1])
    assert [d['id'] for d in db.search(where('tags').any(['x']))] == [2]
    assert db.get(where('tags').any(['x']))['id'] == 2


def test_query_test_receives_field_value_with_list_args():
    def in_allowed(value, allowed):
        return value in allowed

    db = TinyDB(storage=MemoryStorage)
    db.insert({'val': 'a', 'items': ['a', 'b']})
    db.insert({'val': 'c', 'items': ['c']})

    q = Query().val.test(in_allowed, ['a', 'b'])
    assert q.is_cacheable()
    assert [d['val'] for d in db.search(q)] == ['a']
    assert db.get(q)['val'] == 'a'

    q2 = Query().items.all(['a', 'b'])
    assert [d['val'] for d in db.search(q2)] == ['a']
