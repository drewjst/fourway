import toolz
from toolz import _signatures as _sigs


def test_signature_or_spec_returns_none_for_uninspectable():
    for obj in (1, None, 'not callable'):
        res = _sigs.signature_or_spec(obj)
        assert res is None
        assert not isinstance(res, BaseException)


def test_curry_does_not_cache_exception_objects():
    class NoSig(object):
        pass

    # A curry whose underlying func has a valid signature caches a real spec;
    # an uninspectable value must never produce a stored exception instance.
    res = _sigs.signature_or_spec(NoSig())
    assert not isinstance(res, BaseException)
