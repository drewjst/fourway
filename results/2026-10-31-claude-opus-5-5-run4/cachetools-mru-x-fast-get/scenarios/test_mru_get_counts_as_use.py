import pytest

from cachetools import MRUCache


def test_get_marks_item_most_recently_used_for_eviction():
    cache = MRUCache(maxsize=2)
    cache[1] = 1
    cache[2] = 2
    assert cache.get(1) == 1  # 1 becomes the most recently used
    cache[3] = 3  # must evict the most recently used item, i.e. 1
    assert 1 not in cache
    assert 2 in cache
    assert 3 in cache
    assert len(cache) == 2


def test_get_marks_item_most_recently_used_for_popitem():
    cache = MRUCache(maxsize=3)
    cache[1] = 1
    cache[2] = 2
    cache[3] = 3
    assert cache.get(1) == 1
    assert cache.popitem() == (1, 1)
    assert cache.popitem() == (3, 3)
    assert cache.popitem() == (2, 2)


def test_get_matches_getitem_semantics():
    via_get = MRUCache(maxsize=3)
    via_getitem = MRUCache(maxsize=3)
    for c in (via_get, via_getitem):
        c[1] = 1
        c[2] = 2
        c[3] = 3
    assert via_get.get(2) == 2
    assert via_getitem[2] == 2
    assert via_get.get(99, 'd') == 'd'
    assert via_get.popitem() == via_getitem.popitem() == (2, 2)
    via_get[4] = 4
    via_getitem[4] = 4
    assert sorted(via_get) == sorted(via_getitem)


def test_get_missing_returns_default_without_disturbing_order():
    cache = MRUCache(maxsize=2)
    cache[1] = 1
    cache[2] = 2
    assert cache.get(1) == 1
    assert cache.get(42) is None
    assert cache.get(42, 'x') == 'x'
    assert cache.popitem() == (1, 1)
