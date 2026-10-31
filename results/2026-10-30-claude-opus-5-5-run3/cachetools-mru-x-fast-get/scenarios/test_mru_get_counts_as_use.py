import cachetools


def _mru(maxsize):
    return cachetools.MRUCache(maxsize=maxsize)


def test_mru_get_marks_key_most_recently_used_for_eviction():
    cache = _mru(2)
    cache[1] = 1
    cache[2] = 2
    assert cache.get(1) == 1  # 1 is now the most recently used
    cache[3] = 3  # must evict the most recently used item, i.e. 1
    assert len(cache) == 2
    assert 1 not in cache
    assert 2 in cache
    assert 3 in cache


def test_mru_get_affects_popitem_order():
    cache = _mru(3)
    cache[1] = 1
    cache[2] = 2
    cache[3] = 3
    assert cache.get(1) == 1
    assert cache.popitem() == (1, 1)
    assert cache.popitem() == (3, 3)
    assert cache.popitem() == (2, 2)


def test_mru_get_matches_getitem_semantics():
    via_get = _mru(3)
    via_item = _mru(3)
    for c in (via_get, via_item):
        c[1] = 1
        c[2] = 2
        c[3] = 3
    assert via_get.get(2) == 2
    assert via_item[2] == 2
    # a miss through get() returns the default and touches nothing
    assert via_get.get(99, 'd') == 'd'
    assert via_get.popitem() == via_item.popitem() == (2, 2)
    assert via_get.popitem() == via_item.popitem()
