import pytest

import cachetools


def _require():
    assert hasattr(cachetools.Cache, "peek"), "Cache.peek() missing"
    cls = getattr(cachetools, "MRUCache", None)
    if cls is None:
        pytest.skip("MRUCache not available on this tree")
    return cls


def test_peek_does_not_count_as_use_in_mru():
    MRUCache = _require()
    cache = MRUCache(maxsize=2)
    cache[1] = 1
    cache[2] = 2  # 2 is most recently used
    assert cache.peek(1) == 1  # must NOT make 1 the most recently used
    cache[3] = 3  # MRU eviction must remove 2, not 1
    assert 1 in cache
    assert 3 in cache
    assert 2 not in cache
    assert len(cache) == 2


def test_peek_preserves_mru_popitem_order():
    MRUCache = _require()
    cache = MRUCache(maxsize=3)
    cache[1] = 1
    cache[2] = 2
    cache[3] = 3
    assert cache.peek(1) == 1
    assert cache.peek(2) == 2
    assert cache.popitem() == (3, 3)
    assert cache.popitem() == (2, 2)
    assert cache.popitem() == (1, 1)


def test_peek_missing_on_mru_does_not_call_missing():
    MRUCache = _require()
    calls = []

    class DefaultMRU(MRUCache):
        def __missing__(self, key):
            calls.append(key)
            self[key] = key
            return key

    cache = DefaultMRU(maxsize=2)
    cache[1] = 1
    assert cache.peek(5) is None
    assert cache.peek(5, 0) == 0
    assert calls == []
    assert 5 not in cache
    assert len(cache) == 1
