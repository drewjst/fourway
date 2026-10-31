from collections import defaultdict
from toolz.dicttoolz import assoc, assoc_in, update_in


def test_assoc_values_and_immutability():
    d = {'x': 1, 'y': 2}
    snapshot = dict(d)
    r1 = assoc(d, 'x', 5)
    r2 = assoc(d, 'z', 9)
    assert r1 == {'x': 5, 'y': 2}
    assert r2 == {'x': 1, 'y': 2, 'z': 9}
    assert d == snapshot
    assert r1 is not d and r2 is not d

    nested = {'a': {'b': 1}}
    out = assoc_in(nested, ['a', 'c'], 3)
    assert out == {'a': {'b': 1, 'c': 3}}
    assert nested == {'a': {'b': 1}}
    assert update_in({}, ['p', 'q'], str, default=7) == {'p': {'q': '7'}}


def test_assoc_respects_factory_type():
    src = defaultdict(int, {1: 2})
    out = assoc(src, 3, 4, factory=lambda: defaultdict(int))
    assert isinstance(out, defaultdict)
    assert out.default_factory is int
    assert dict(out) == {1: 2, 3: 4}
    assert out[99] == 0
    assert dict(src) == {1: 2}
