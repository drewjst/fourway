import builtins
import inspect
import typing
from toolz.functoolz import compose, curry


def f(x: int) -> str:
    return str(x)


def g(y: str) -> float:
    return float(len(y))


def _from_sig(c):
    sig = inspect.signature(c)
    rv = {k: p.annotation for k, p in sig.parameters.items()
          if p.annotation is not p.empty}
    if sig.return_annotation is not sig.empty:
        rv['return'] = sig.return_annotation
    return rv


def test_compose_annotations_basic_and_curried():
    assert compose(g, f).__annotations__ == {'x': int, 'return': float}
    assert typing.get_type_hints(compose(g, f)) == {'x': int, 'return': float}
    c = compose(g, curry(f))
    assert c.__annotations__ == {'x': int, 'return': float}
    assert c.__annotations__ == _from_sig(c)
    assert compose(compose(g, f), compose(f, len)).__annotations__ == {
        'return': float}


def test_compose_annotations_with_builtin_mapping_constructors():
    ctors = [dict]
    if hasattr(builtins, 'frozendict'):
        ctors.append(builtins.frozendict)
    for ctor in ctors:
        # builtin at the start: only the return annotation survives
        assert compose(g, ctor).__annotations__ == {'return': float}
        # builtin at the end: only parameter annotations survive
        assert compose(ctor, f).__annotations__ == {'x': int}
        # curried builtin in a composition
        assert compose(g, curry(ctor)).__annotations__ == {'return': float}
        assert compose(curry(ctor), f).__annotations__ == {'x': int}
        assert typing.get_type_hints(compose(ctor, f)) == {'x': int}
