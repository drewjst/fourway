from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage
from tinydb.utils import LRUCache


def test_lru_evicts_least_recent_after_access():
    cache = LRUCache(capacity=2)
    cache['a'] = 1
    cache['b'] = 2
    assert cache['a'] == 1
    cache['c'] = 3
    assert 'b' not in cache
    assert cache.lru == ['a', 'c']
    assert cache['a'] == 1 and cache['c'] == 3


def test_table_query_cache_keeps_recently_hit_query():
    db = TinyDB(storage=MemoryStorage)
    table = db.table('t', cache_size=2)
    table.insert_multiple({'int': i} for i in range(3))
    q1 = where('int') == 1
    q2 = where('int') == 2
    q0 = where('int') == 0
    assert len(table.search(q1)) == 1
    assert len(table.search(q2)) == 1
    r = table.search(q1)  # hit, becomes most recent
    assert r == [{'int': 1}]
    r.append('junk')
    assert len(table.search(q0)) == 1
    assert q1 in table._query_cache
    assert q2 not in table._query_cache
    assert table.search(q1) == [{'int': 1}]
