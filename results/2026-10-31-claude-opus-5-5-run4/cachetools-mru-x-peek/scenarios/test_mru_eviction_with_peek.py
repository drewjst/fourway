import pytest

import cachetools


def _require_mru():
    cls = getattr(cachetools, "MRUCache", None)
    assert cls is not None, "MRUCache is missing"
    return cls


def _peek_or_skip():
    if not hasattr(cachetools.Cache, "peek"):
        pytest.skip("Cache.peek() not available in this tree")


def test_mru_popitem_order_unaffected_by_peek():
    MRUCache = _require_mru()
    _peek_or_skip()
    cache = MRUCache(maxsize=3)
    cache[1] = 1
    cache[2] = 2
    cache[3] = 3
    cache[1]  # real use: 1 becomes most recently used
    assert cache.peek(2) == 2
    assert cache.peek(3) == 3
    assert cache.popitem() == (1, 1)
    assert cache.popitem() == (3, 3)
    assert cache.popitem() == (2, 2)


def test_mru_getsizeof_eviction_with_peek():
    MRUCache = _require_mru()
    _peek_or_skip()
    cache = MRUCache(maxsize=5, getsizeof=lambda x: x)
    cache[1] = 1
    cache[2] = 2
    assert cache.peek(1) == 1
    cache[3] = 3  # needs room: evicts the MRU item, which is still 2
    assert 2 not in cache
    assert 1 in cache
    assert 3 in cache
    assert cache.currsize == 4
    assert len(cache) == 2
