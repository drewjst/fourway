import pickle
import pytest
import toolz
import toolz.curried
from toolz import curry
from toolz.dicttoolz import merge, merge_with


def test_merge_rejects_unknown_keyword_with_message():
    with pytest.raises(TypeError) as info:
        merge({1: 2}, {2: 3}, factoryy=dict)
    assert str(info.value) == "merge() got an unexpected keyword argument 'factoryy'"
    with pytest.raises(TypeError) as info:
        merge_with(sum, {1: 2}, bogus=1)
    assert str(info.value) == "merge_with() got an unexpected keyword argument 'bogus'"


def test_curry_pickle_roundtrip():
    f = curry(map)(str)
    g = pickle.loads(pickle.dumps(f))
    assert list(f((1, 2, 3))) == list(g((1, 2, 3)))
    m = pickle.loads(pickle.dumps(toolz.curried.merge))
    assert m is toolz.curried.merge
    a = pickle.loads(pickle.dumps(toolz.curried.assoc))
    assert a({'x': 1}, 'y', 2) == {'x': 1, 'y': 2}
