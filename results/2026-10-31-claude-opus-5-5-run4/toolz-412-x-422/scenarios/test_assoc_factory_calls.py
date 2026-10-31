from toolz.dicttoolz import assoc, assoc_in, update_in


def _counting_factory():
    calls = [0]

    def factory():
        calls[0] += 1
        return dict()
    return factory, calls


def test_assoc_calls_factory_once():
    factory, calls = _counting_factory()
    d = {'x': 1, 'y': 2}
    result = assoc(d, 'z', 3, factory=factory)
    assert result == {'x': 1, 'y': 2, 'z': 3}
    assert calls[0] == 1

    factory, calls = _counting_factory()
    result = assoc(d, 'x', 10, factory=factory)
    assert result == {'x': 10, 'y': 2}
    assert calls[0] == 1


def test_nested_updates_call_factory_once_per_level():
    factory, calls = _counting_factory()
    d = {'a': {'b': 1}, 'c': 0}
    result = update_in(d, ['a', 'b'], lambda v: v + 1, factory=factory)
    assert result == {'a': {'b': 2}, 'c': 0}
    assert calls[0] == 2

    factory, calls = _counting_factory()
    result = assoc_in(d, ['a', 'b'], 42, factory=factory)
    assert result == {'a': {'b': 42}, 'c': 0}
    assert calls[0] == 2
