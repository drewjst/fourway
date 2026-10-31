import pytest

from semver import Version


@pytest.mark.parametrize(
    "version,token,expected",
    [
        ("3.4.5-rc.1+build.9", "build", "3.4.5-rc.1+build.10"),
        ("3.4.5-rc.1+0009.dev", "build", "3.4.5-rc.1+0010.dev"),
        ("3.4.5-rc.1", "build", "3.4.5-rc.1+build.1"),
        ("3.4.5", "", "3.4.5+1"),
        ("3.4.5", None, "3.4.5+build.1"),
        ("3.4.5", "b", "3.4.5+b.1"),
    ],
)
def test_bump_build_results_and_precedence(version, token, expected):
    v = Version.parse(version)
    result = v.bump_build(token)
    assert str(result) == expected
    assert result.compare(v) == 0
    assert result.prerelease == v.prerelease
    assert str(v) == version


def test_bump_build_keeps_subclass_and_chains():
    class MyVersion(Version):
        pass

    v = MyVersion.parse("1.2.3-rc.2+build.1")
    r = v.bump_build().bump_build()
    assert type(r) is MyVersion
    assert str(r) == "1.2.3-rc.2+build.3"
    assert str(v) == "1.2.3-rc.2+build.1"
