from semver import Version


class Sub(Version):
    pass


def test_subclass_parse_returns_subclass_instance():
    v = Sub.parse('1.2.3-rc.1+build.9')
    assert isinstance(v, Sub)
    assert type(Sub.parse('1.2', optional_minor_and_patch=True)) is Sub


def test_default_bumps_increment_once():
    v = Sub.parse('3.4.5-rc.1+build.9')
    b = v.bump_build()
    assert b.build == 'build.10'
    assert b.prerelease == 'rc.1'
    assert type(b) is Sub
    p = v.bump_prerelease()
    assert p.prerelease == 'rc.2'
    assert p.build is None
    assert Sub.parse('3.4.5').bump_build('b').build == 'b.1'
    assert Sub.parse('3.4.5').bump_prerelease('dev').prerelease == 'dev.1'
    assert str(v) == '3.4.5-rc.1+build.9'
