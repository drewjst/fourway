import inspect
from collections import OrderedDict

import toolz
from toolz import compose, dissoc


class Record(dict):
    without_keys = compose(dict, dissoc)
    size_without = compose(len, dissoc)


def test_compose_binds_as_method_on_dict_subclass():
    rec = Record({'a': 1, 'b': 2, 'c': 3})
    assert rec.without_keys('a') == {'b': 2, 'c': 3}
    assert rec.without_keys('a', 'b', 'c') == {}
    assert rec.size_without('a', 'b') == 1
    assert rec == {'a': 1, 'b': 2, 'c': 3}


def test_compose_signature_tracks_dissoc_signature():
    composed = compose(len, dissoc)
    sig = inspect.signature(composed)
    assert sig.parameters == inspect.signature(dissoc).parameters
    bound_params = list(inspect.signature(Record({'a': 1}).size_without).parameters)
    assert bound_params == list(inspect.signature(dissoc).parameters)[1:]


def test_compose_equality_and_hash_with_curried_dissoc():
    c1 = compose(dict, toolz.curry(dissoc, factory=OrderedDict))
    c2 = compose(dict, toolz.curry(dissoc, factory=OrderedDict))
    c3 = compose(dict, toolz.curry(dissoc, factory=dict))
    assert c1 == c2
    assert not (c1 != c2)
    assert hash(c1) == hash(c2)
    assert c1 != c3
    assert len({c1, c2, c3}) == 2
