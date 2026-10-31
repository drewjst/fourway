import builtins
import toolz
import toolz._signatures as _sigs
from toolz.functoolz import (curry, is_valid_args, is_partial_args,
                             has_keywords, num_required_args, compose)


def _frozendict_specs():
    info = _sigs.module_info[builtins]
    assert 'frozendict' in info
    return tuple(_sigs.expand_sig(s) for s in info['frozendict'])


def test_frozendict_registry_entry_has_dict_semantics():
    sigs = _frozendict_specs()

    def valid(args, kwargs):
        return any(_sigs.check_valid(s, args, kwargs) for s in sigs)

    def partial_(args, kwargs):
        return any(_sigs.check_partial(s, args, kwargs) for s in sigs)

    assert valid((), {})
    assert valid(({'a': 1},), {})
    assert valid((), {'a': 1})
    assert valid(({'a': 1},), {'b': 2})
    assert not valid(({}, {}), {})
    assert partial_((), {})
    assert partial_(({'a': 1},), {})
    assert not partial_(({}, {}), {})


class _NoSig:
    """Callable whose signature cannot be inspected, like a C builtin."""

    def __call__(self, *args, **kwargs):
        d = {}
        if args:
            d.update(args[0])
        d.update(kwargs)
        return tuple(sorted(d.items()))

    @property
    def __signature__(self):
        raise ValueError('no signature')


def test_frozendict_specs_drive_introspection_and_curry():
    sigs = _frozendict_specs()
    fake = _NoSig()
    _sigs.signatures[fake] = sigs
    try:
        assert is_valid_args(fake, (), {}) is True
        assert is_valid_args(fake, ({'a': 1},), {}) is True
        assert is_valid_args(fake, (), {'a': 1}) is True
        assert is_valid_args(fake, ({}, {}), {}) is False
        assert is_partial_args(fake, ({}, {}), {}) is False
        assert has_keywords(fake) is True
        assert num_required_args(fake) is None
        cf = curry(fake)
        assert cf({'a': 1}) == (('a', 1),)
        assert cf(b=2) == (('b', 2),)
        # composing with such a callable must still be callable
        assert compose(len, cf)({'a': 1, 'b': 2}) == 2
    finally:
        del _sigs.signatures[fake]

    if hasattr(builtins, 'frozendict'):
        fd = builtins.frozendict
        assert fd in _sigs.signatures
        assert is_valid_args(fd, (), {}) is True
        assert is_valid_args(fd, ({'a': 1},), {}) is True
        assert is_valid_args(fd, ({}, {}), {}) is False
