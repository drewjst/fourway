from semver import Version


def test_nonnumeric_prerelease_bump_then_build_is_newer():
    v = Version.parse("3.4.5-rc9+build.3")
    pre = v.bump_prerelease()
    assert str(pre) == "3.4.5-rc9.0"
    assert pre.compare(v) == 1
    built = pre.bump_build()
    assert str(built) == "3.4.5-rc9.0+build.1"
    assert built.prerelease == "rc9.0"
    assert built.compare(v) == 1


def test_bump_when_empty_then_build():
    v = Version.parse("3.4.5+build.7")
    pre = v.bump_prerelease(bump_when_empty=True)
    assert pre == Version(3, 4, 6, "rc.1")
    assert pre.build is None
    built = pre.bump_build()
    assert str(built) == "3.4.6-rc.1+build.1"
    assert built.compare(v) == 1
