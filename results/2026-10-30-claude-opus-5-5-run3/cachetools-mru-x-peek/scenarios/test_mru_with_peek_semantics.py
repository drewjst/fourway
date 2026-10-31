import pytest

import cachetools


def _require():
    cls = cachetools.MRUCache  # AttributeError on trees without change A
    if not hasattr(cachetools.Cache, "peek"):
        pytest.skip("Cache.peek not available on this tree")
    return cls


def test_get_still_counts_as_use_with_peeks_interleaved():
    MRUCache = _require()
    cache = MRUCache(maxsize=3)
    cache[1] = 1
    cache[2] = 2
    cache[3] = 3
    assert cache[1] == 1  # real use: 1 becomes most recently used
    assert cache.peek(2) == 2  # not a use
    assert cache.peek(3) == 3  # not a use
    assert cache.popitem() == (1, 1)
    assert cache.popitem() == (3, 3)
    assert cache.popitem() == (2, 2)


def test_update_counts_as_use_after_peek():
    MRUCache = _require()
    cache = MRUCache(maxsize=2)
    cache[1] = 1
    cache[2] = 2
    assert cache.peek(2) == 2
    cache[1] = "updated"  # update is a use: 1 is now MRU
    assert cache.peek(1) == "updated"
    cache[3] = 3  # evicts 1
    assert 1 not in cache
    assert cache.peek(2) == 2
    assert cache.peek(3) == 3
