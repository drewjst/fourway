import inspect
import typing
from collections.abc import Callable, Mapping, MutableMapping

from tinydb.table import Table


def _flatten(x):
    if isinstance(x, (list, tuple)):
        out = []
        for e in x:
            out.extend(_flatten(e))
        return out
    return [x]


def _callable_params(ann):
    found = []
    origin = typing.get_origin(ann)
    args = typing.get_args(ann)
    if origin is Callable:
        if args:
            found.append(_flatten(args[0]))
        return found
    for a in args:
        for sub in _flatten(a):
            found.extend(_callable_params(sub))
    return found


def test_update_transform_hint_is_mutable_mapping():
    ann = inspect.signature(Table.update).parameters['fields'].annotation
    params = _callable_params(ann)
    assert params, 'expected a Callable in the fields annotation'
    for p in params:
        assert p == [MutableMapping]
        assert Mapping not in p


def test_update_multiple_transform_hint_is_mutable_mapping():
    ann = inspect.signature(Table.update_multiple).parameters['updates'].annotation
    params = _callable_params(ann)
    assert params, 'expected a Callable in the updates annotation'
    for p in params:
        assert p == [MutableMapping]
        assert Mapping not in p
