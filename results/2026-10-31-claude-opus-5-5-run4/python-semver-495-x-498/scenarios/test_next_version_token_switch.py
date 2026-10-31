import pytest

from semver import Version


@pytest.mark.parametrize(
    'current, token, expected',
    [
        ('1.2.3-rc.1', 'alpha', '1.2.4-alpha.1'),
        ('1.2.3-beta.3', 'alpha', '1.2.4-alpha.1'),
        ('1.2.3-rc.1+build.7', 'dev', '1.2.4-dev.1'),
        ('1.2.3-rc3', 'alpha', '1.2.4-alpha.1'),
    ],
)
def test_backward_token_switch_advances_patch(current, token, expected):
    original = Version.parse(current)
    result = original.next_version('prerelease', token)
    assert str(result) == expected
    assert result > original
    assert result.build is None
    assert str(original) == current
    assert Version.is_valid(str(result)) is True
    assert Version.is_valid(str(result).encode('UTF-8')) is True
    assert Version.parse(str(result).encode('UTF-8')) > Version.parse(current.encode('UTF-8'))


def test_backward_token_switch_preserves_subclass():
    class MyVersion(Version):
        pass

    original = MyVersion.parse('1.2.3-rc.1')
    result = original.next_version('prerelease', 'alpha')
    assert type(result) is MyVersion
    assert str(result) == '1.2.4-alpha.1'
    assert MyVersion.is_valid(str(result).encode('UTF-8'))
