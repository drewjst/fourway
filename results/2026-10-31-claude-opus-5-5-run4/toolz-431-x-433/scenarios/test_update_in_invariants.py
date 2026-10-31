from collections import defaultdict

from toolz.dicttoolz import update_in, assoc_in


def inc(x):
    return x + 1


def test_update_in_no_mutation_and_copies():
    inner = {'b': 1, 'c': 2}
    d = {'a': inner, 'x': 0}
    r = update_in(d, ['a', 'b'], inc)
    assert r == {'a': {'b': 2, 'c': 2}, 'x': 0}
    assert d == {'a': {'b': 1, 'c': 2}, 'x': 0}
    assert r is not d
    assert r['a'] is not inner
    assert inner == {'b': 1, 'c': 2}


def test_update_in_missing_paths_and_factory():
    assert update_in({'a': 1}, ['b', 'c'], str, default=5) == {'a': 1, 'b': {'c': '5'}}
    assert update_in({1: 'foo'}, [2, 3, 4], inc, 0) == {1: 'foo', 2: {3: {4: 1}}}
    assert assoc_in({'a': {'b': 1}}, ('a', 'b'), 9) == {'a': {'b': 9}}
    factory = lambda: defaultdict(int)
    r = update_in(defaultdict(int, {'t': 1}), ['v', 'a'], inc, 0, factory=factory)
    assert isinstance(r, defaultdict)
    assert isinstance(r['v'], defaultdict)
    assert dict(r['v']) == {'a': 1}
    assert r['t'] == 1
