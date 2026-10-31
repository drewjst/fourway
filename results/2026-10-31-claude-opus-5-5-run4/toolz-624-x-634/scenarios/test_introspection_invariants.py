import inspect
import toolz
import toolz.functoolz as ftz
import toolz._signatures as _sigs
from toolz.functoolz import (compose, curry, is_partial_args, is_valid_args,
                             num_required_args, Compose)


def f(x: int) -> str:
    return str(x)


def g(y: str) -> float:
    return float(len(y))


def test_functoolz_public_callables_remain_introspectable():
    missing = []
    for name, func in vars(ftz).items():
        if name.startswith('_') and not name.startswith('__'):
            continue
        try:
            if issubclass(func, BaseException):
                continue
        except TypeError:
            pass
        try:
            if (callable(func)
                    and func.__module__ is not None
                    and 'toolz.functoolz' in func.__module__
                    and is_partial_args(func, (), {}) is not True):
                missing.append(name)
        except AttributeError:
            continue
    assert missing == []


def test_compose_signature_and_registry_unchanged():
    assert Compose in _sigs.signatures
    assert num_required_args(Compose) == 1
    c = compose(g, f)
    sig = inspect.signature(c)
    assert list(sig.parameters) == ['x']
    assert sig.parameters['x'].annotation is int
    assert sig.return_annotation is float
    assert is_valid_args(c, (1,), {}) is True
    assert is_valid_args(c, (1, 2), {}) is False
    assert c(123) == 3.0
    cd = curry(dict)
    assert cd(a=1) == {'a': 1}
    assert compose(len, cd)({'a': 1, 'b': 2}) == 2
