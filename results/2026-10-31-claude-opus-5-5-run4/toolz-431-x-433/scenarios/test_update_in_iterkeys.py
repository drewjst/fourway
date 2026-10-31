from collections import defaultdict

from toolz.dicttoolz import update_in


def inc(x):
    return x + 1


def test_update_in_accepts_generator_keys():
    d = {'a': {'b': 1, 'c': 2}, 'x': 0}
    keys = (k for k in ['a', 'b'])
    r = update_in(d, keys, inc)
    assert r == {'a': {'b': 2, 'c': 2}, 'x': 0}
    assert d == {'a': {'b': 1, 'c': 2}, 'x': 0}


def test_update_in_iterator_keys_missing_path_with_factory():
    factory = lambda: defaultdict(int)
    r = update_in({}, iter([0, 1]), inc, default=-1, factory=factory)
    assert isinstance(r, defaultdict)
    assert isinstance(r[0], defaultdict)
    assert dict(r[0]) == {1: 0}
