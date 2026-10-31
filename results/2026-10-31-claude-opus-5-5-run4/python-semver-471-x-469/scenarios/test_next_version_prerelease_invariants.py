from semver import Version


def test_prerelease_with_build_finalizes():
    assert str(Version.parse("3.4.5-pre.2+build.4").next_version(part="patch")) == "3.4.5"
    assert str(Version.parse("1.2.3-rc.1+build.5").next_version("patch")) == "1.2.3"
    assert str(Version.parse("1.0.0-rc.1+build.5").next_version("major")) == "1.0.0"
    assert str(Version.parse("0.2.0-rc.1+b.1").next_version("minor")) == "0.2.0"


def test_prerelease_part_examples_stable():
    assert str(Version.parse("0.1.4").next_version("prerelease")) == "0.1.5-rc.1"
    assert str(Version.parse("0.1.5-rc.1").next_version("prerelease")) == "0.1.5-rc.2"
    assert str(Version.parse("1.2.3").next_version("patch")) == "1.2.4"
    assert str(Version.parse("1.2.3").next_version("major")) == "2.0.0"
