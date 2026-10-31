from cachetools import MRUCache


def test_a_read_through_get_counts_as_a_use_when_evicting():
    cache = MRUCache(maxsize=2)
    cache[1] = 1
    cache[2] = 2
    assert cache.get(1) == 1  # 1 is now the most recently used
    cache[3] = 3
    assert 1 not in cache
    assert 2 in cache and 3 in cache
