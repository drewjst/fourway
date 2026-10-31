import pytest

from semver import Version


@pytest.mark.parametrize(
    'current, token',
    [
        ('1.2.3-rc.1', 'alpha'),
        ('1.2.3-alpha.4', 'rc'),
        ('1.2.3-rc.1+build.7', 'dev'),
        ('1.2.3-alphaXbeta9', 'alpha.beta'),
        ('1.2.3-rc.1', '2'),
        ('1.2.3', 'rc'),
        ('1.2.3-rc3', 'rc'),
    ],
)
def test_next_prerelease_is_valid_semver(current, token):
    original = Version.parse(current)
    result = original.next_version('prerelease', token)
    text = str(result)
    assert Version.is_valid(text) is True
    assert Version.is_valid(text.encode('UTF-8')) is True
    assert Version.parse(text.encode('UTF-8')).to_tuple() == result.to_tuple()
    assert result.build is None
    assert str(original) == current


@pytest.mark.parametrize(
    'current, token, expected',
    [
        ('1.2.3-alpha.4', 'rc', '1.2.3-rc.1'),
        ('1.2.3-alpha.1', 'beta', '1.2.3-beta.1'),
        ('1.2.3-rc.3', 'rc', '1.2.3-rc.4'),
        ('0.1.2-rc3', 'rc', '0.1.2-rc4'),
    ],
)
def test_forward_and_same_token_keep_patch(current, token, expected):
    original = Version.parse(current)
    result = original.next_version('prerelease', token)
    assert str(result) == expected
    assert result > original
