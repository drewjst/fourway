from cachetools import LFUCache, LRUCache, TTLCache


def test_lru_and_lfu_get_count_as_use():
    for cls in (LRUCache, LFUCache):
        cache = cls(maxsize=2)
        cache[1] = 1
        cache[2] = 2
        assert cache.get(1) == 1
        cache[3] = 3
        assert 1 in cache
        assert 2 not in cache
        assert cache.get(2, 'd') == 'd'


def test_ttl_get_hides_expired():
    now = [0]
    cache = TTLCache(maxsize=2, ttl=10, timer=lambda: now[0])
    cache[1] = 1
    assert cache.get(1) == 1
    now[0] = 10
    assert cache.get(1) is None
    assert cache.get(1, 'd') == 'd'
