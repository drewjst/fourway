from collections import OrderedDict

from tinydb.utils import LRUCache


class TrackingOD(OrderedDict):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.deleted = []

    def __delitem__(self, key):
        self.deleted.append(key)
        super().__delitem__(key)


def _make():
    cache = LRUCache(capacity=5)
    cache.cache = TrackingOD()
    return cache


def test_get_moves_without_reinsert():
    cache = _make()
    cache['a'] = 1
    cache['b'] = 2
    cache['c'] = 3
    assert cache.get('a') == 1
    assert cache.cache.deleted == []
    assert cache.lru == ['b', 'c', 'a']


def test_set_existing_moves_without_reinsert():
    cache = _make()
    cache['a'] = 1
    cache['b'] = 2
    cache['a'] = 1
    assert cache.cache.deleted == []
    assert cache.lru == ['b', 'a']
