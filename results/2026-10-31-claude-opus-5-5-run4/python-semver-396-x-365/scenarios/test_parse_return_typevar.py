import inspect
import typing

from semver import Version


class Sub(Version):
    pass


def test_parse_return_annotation_is_typevar_bound_to_version():
    sig = inspect.signature(Version.parse)
    ann = sig.return_annotation
    assert isinstance(ann, typing.TypeVar)
    bound = ann.__bound__
    assert bound is not None
    name = getattr(bound, '__forward_arg__', getattr(bound, '__name__', None))
    assert name == 'Version'


def test_parse_on_subclass_then_bump_keeps_subclass():
    v = Sub.parse('1.2.3')
    assert type(v) is Sub
    assert type(v.bump_prerelease()) is Sub
    assert type(v.bump_build()) is Sub
    assert str(v.bump_prerelease()) == '1.2.3-rc.1'
    assert str(v.bump_build()) == '1.2.3+build.1'
