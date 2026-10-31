import inspect
import typing

from semver import Version


def _annotation_args():
    func = Version.is_valid.__func__
    ann = inspect.signature(func).parameters['version'].annotation
    if isinstance(ann, str):
        hints = typing.get_type_hints(func)
        ann = hints['version']
    args = typing.get_args(ann)
    return ann, args


def test_is_valid_annotation_includes_bytes():
    ann, args = _annotation_args()
    assert bytes in args or ann is bytes, ann
    assert str in args or ann is str, ann


def test_is_valid_bytes_on_token_switch_results():
    ann, args = _annotation_args()
    assert bytes in args
    for current, token in [('1.2.3-rc.1', 'alpha'), ('1.2.3-alpha.4', 'rc'), ('1.2.3-rc.1+build.7', 'dev')]:
        result = Version.parse(current).next_version('prerelease', token)
        encoded = str(result).encode('UTF-8')
        assert Version.is_valid(encoded) is True
        assert Version.parse(encoded) == result
    assert Version.is_valid(b'\xff') is False
