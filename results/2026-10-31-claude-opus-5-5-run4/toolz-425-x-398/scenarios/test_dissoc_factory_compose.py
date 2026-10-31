from collections import OrderedDict

import toolz
from toolz import compose, dissoc


def test_curried_dissoc_with_factory_as_compose_head():
    from toolz.curried import dissoc as cdissoc
    assert isinstance(cdissoc, toolz.curry)
    stage = cdissoc(factory=OrderedDict)
    assert isinstance(stage, toolz.curry)
    src = OrderedDict([('a', 1), ('b', 2), ('c', 3)])
    keys_after = compose(list, stage)(src, 'b')
    assert keys_after == ['a', 'c']
    kind = compose(type, stage)(src, 'b')
    assert kind is OrderedDict
    # input untouched
    assert list(src.items()) == [('a', 1), ('b', 2), ('c', 3)]


def test_dissoc_factory_many_keys_path_inside_compose():
    src = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5}
    pipeline = compose(lambda m: (type(m), dict(m)),
                       lambda d, *ks: dissoc(d, *ks, factory=OrderedDict))
    kind, val = pipeline(src, 'a', 'b', 'c', 'd', 'zz')
    assert kind is OrderedDict
    assert val == {'e': 5}
    kind, val = pipeline(src, 'a', 'b', 'c', 'd', 'e', 'x', 'y')
    assert kind is OrderedDict
    assert val == {}
    assert src == {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5}
