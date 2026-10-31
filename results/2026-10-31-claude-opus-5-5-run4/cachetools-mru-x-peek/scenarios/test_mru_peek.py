import pytest

import cachetools


def _require_peek():
    assert hasattr(cachetools.Cache, "peek"), "Cache.peek() is missing"


def _mru_or_skip():
    cls = getattr(cachetools, "MRUCache", None)
    if cls is None:
        pytest.skip("MRUCache not available in this tree")
    return cls


def test_peek_does_not_count_as_use_in_mru():
    _require_peek()
    MRUCache = _mru_or_skip()
    cache = MRUCache(maxsize=2)
    cache[1] = 1
    cache[2] = 2
    # peeking 1 must not make it the most recently used item
    assert cache.peek(1) == 1
    assert cache.peek(1) == 1
    cache[3] = 3
    assert 2 not in cache
    assert 1 in cache
    assert 3 in cache
    assert len(cache) == 2


def test_peek_missing_in_mru_subclass_does_not_store():
    _require_peek()
    MRUCache = _mru_or_skip()
    calls = []

    class DefaultMRU(MRUCache):
        def __missing__(self, key):
            calls.append(key)
            self[key] = key
            return key

    cache = DefaultMRU(maxsize=2)
    cache[1] = 1
    assert cache.peek(5) is None
    assert cache.peek(5, "x") == "x"
    assert calls == []
    assert 5 not in cache
    assert len(cache) == 1
    assert cache.currsize == 1
    assert cache.popitem() == (1, 1)
    with pytest.raises(KeyError):
        cache.popitem()
