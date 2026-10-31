from toolz import compose, dissoc


class Holder(dict):
    pruned = compose(dict, dissoc)
    spruned = staticmethod(compose(dict, dissoc))


def test_composed_dissoc_removes_exactly_requested_keys():
    pipeline = compose(dict, dissoc)
    base = dict((k, i) for i, k in enumerate('abcdefghij'))
    snapshot = dict(base)
    all_keys = list(base)
    for n in range(0, len(all_keys) + 3):
        keys = all_keys[:n] + ['missing%d' % i for i in range(max(0, n - len(all_keys)))]
        expected = dict((k, v) for k, v in base.items() if k not in keys)
        assert pipeline(base, *keys) == expected
        assert base == snapshot


def test_class_level_and_static_access_of_composed_dissoc():
    h = Holder({'a': 1, 'b': 2, 'c': 3})
    assert Holder.pruned(h, 'a') == {'b': 2, 'c': 3}
    assert Holder.spruned({'x': 1, 'y': 2}, 'y') == {'x': 1}
    assert h.spruned({'x': 1, 'y': 2}, 'x', 'y') == {}
    assert h == {'a': 1, 'b': 2, 'c': 3}
