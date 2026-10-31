from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage
from tinydb.table import Document
from tinydb.utils import LRUCache


def test_query_cache_refreshed_after_mixed_batch():
    db = TinyDB(storage=MemoryStorage)
    db.insert_multiple([{'k': 1}])

    q = where('k').exists()
    assert db.count(q) == 1
    assert db.count(q) == 1  # cached

    ids = db.insert_multiple([
        {'k': 2},
        Document({'k': 3}, 10),
        {'k': 4},
    ])

    assert len(ids) == 3
    assert len(set(ids)) == 3
    assert 10 in ids

    results = db.search(q)
    assert len(results) == 4
    assert sorted(d['k'] for d in results) == [1, 2, 3, 4]
    assert len({d.doc_id for d in results}) == 4
    assert db.get(doc_id=10) == {'k': 3}

    # A follow-up insert must not clobber anything
    new_id = db.insert({'k': 5})
    assert new_id not in {d.doc_id for d in results}
    assert db.count(q) == 5


def test_lru_capacity_respected_with_none_values():
    cache = LRUCache(capacity=2)
    cache['a'] = None
    cache['b'] = None
    cache['c'] = None

    assert len(cache) == 2
    assert 'a' not in cache
    assert 'b' in cache and 'c' in cache
    assert cache.lru == ['b', 'c']

    cache['b'] = None  # re-set existing key moves it to MRU end
    assert cache.lru == ['c', 'b']
    assert len(cache) == 2
