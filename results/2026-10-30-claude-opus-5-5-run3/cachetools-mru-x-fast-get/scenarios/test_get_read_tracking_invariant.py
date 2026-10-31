from cachetools import LRUCache, LFUCache


def test_lru_get_counts_as_use():
    cache = LRUCache(maxsize=2)
    cache[1] = 1
    cache[2] = 2
    assert cache.get(1) == 1
    cache[3] = 3
    assert 1 in cache
    assert 2 not in cache


def test_lfu_get_counts_as_use_and_default_on_miss():
    cache = LFUCache(maxsize=2)
    cache[1] = 1
    cache[2] = 2
    assert cache.get(1) == 1
    assert cache.get(42, 'x') == 'x'
    cache[3] = 3
    assert 1 in cache
    assert 2 not in cache
