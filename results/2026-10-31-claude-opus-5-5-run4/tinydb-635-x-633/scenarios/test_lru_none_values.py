import pytest

from tinydb.utils import LRUCache


def test_none_value_is_present_and_readable():
    cache = LRUCache(capacity=3)
    cache['a'] = None

    assert 'a' in cache
    assert cache['a'] is None
    assert cache.get('a', 'default') is None
    assert cache.get('missing', 'default') == 'default'
    with pytest.raises(KeyError):
        cache['missing']


def test_none_value_participates_in_lru_ordering():
    cache = LRUCache(capacity=2)
    cache['a'] = None
    cache['b'] = 1

    # Accessing the None entry must bump it to the MRU end
    assert cache.get('a', 'default') is None
    assert cache.lru == ['b', 'a']

    # So inserting a new key evicts 'b', not 'a'
    cache['c'] = 2
    assert 'b' not in cache
    assert 'a' in cache
    assert cache['a'] is None
    assert cache.lru == ['a', 'c']
