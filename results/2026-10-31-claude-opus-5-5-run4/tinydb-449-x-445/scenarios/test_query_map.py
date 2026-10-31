from tinydb import TinyDB, Query, where
from tinydb.storages import MemoryStorage
from tinydb.operations import subtract


def test_map_eq_and_chain():
    double = lambda x: x + x
    q = Query().value.map(double) == 10
    assert q({'value': 5})
    assert not q({'value': 10})
    assert not q({'other': 5})

    rekey = lambda x: {'y': x['a'], 'z': x['b']}
    q2 = Query().map(rekey).z == 10
    assert q2({'a': 5, 'b': 10})
    assert not q2({'a': 10, 'b': 5})


def test_map_cacheability_propagates_through_combinators():
    q = where('val').map(lambda x: x + 1) == 6
    plain = where('x') == 1
    assert plain.is_cacheable()
    assert not q.is_cacheable()
    assert not (q & plain).is_cacheable()
    assert not (plain | q).is_cacheable()
    assert not (~q).is_cacheable()
    assert ((where('a') == 1) | (where('b') == 2)).is_cacheable()
    assert (q & plain)({'val': 5, 'x': 1})
    assert not (q & plain)({'val': 5, 'x': 2})


def test_map_query_not_cached_in_table():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'val': 5})
    state = {'add': 5}
    q = where('val').map(lambda x: x + state['add']) == 10
    assert db.count(q) == 1
    state['add'] = 10
    assert db.count(q) == 0
    assert len(db._query_cache) == 0


def test_subtract_with_map_condition():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'val': 5, 'tag': 'a'})
    db.insert({'val': 7, 'tag': 'b'})
    updated = db.update(subtract('val', 3), where('val').map(lambda x: x * 2) == 10)
    assert updated == [1]
    assert db.get(where('tag') == 'a')['val'] == 2
    assert db.get(where('tag') == 'b')['val'] == 7
