import cachetools


def test_all_exports_resolve():
    for name in cachetools.__all__:
        assert hasattr(cachetools, name), name


def test_get_still_counts_as_use():
    # LRU: get() makes 1 recently used, so 2 is evicted
    lru = cachetools.LRUCache(maxsize=2)
    lru[1] = 1
    lru[2] = 2
    assert lru.get(1) == 1
    lru[3] = 3
    assert 1 in lru and 3 in lru and 2 not in lru

    # LFU: get() bumps 1's frequency, so 2 is evicted
    lfu = cachetools.LFUCache(maxsize=2)
    lfu[1] = 1
    lfu[2] = 2
    assert lfu.get(1) == 1
    lfu[3] = 3
    assert 1 in lfu and 3 in lfu and 2 not in lfu

    mru_cls = getattr(cachetools, "MRUCache", None)
    if mru_cls is not None:
        # MRU: get() makes 1 most recently used, so 1 is evicted
        mru = mru_cls(maxsize=2)
        mru[1] = 1
        mru[2] = 2
        assert mru.get(1) == 1
        mru[3] = 3
        assert 1 not in mru and 2 in mru and 3 in mru
