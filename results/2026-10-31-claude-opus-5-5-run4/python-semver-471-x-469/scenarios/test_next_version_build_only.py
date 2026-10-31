from argparse import Namespace

import semver
from semver import Version
from semver.cli import cmd_nextver


def test_build_only_versions_are_bumped():
    assert str(semver.Version.parse("1.2.3+build.5").next_version("patch")) == "1.2.4"
    assert str(semver.Version.parse("3.4.5+build.4").next_version(part="patch")) == "3.4.6"
    assert str(semver.Version.parse("1.2.0+build.5").next_version("minor")) == "1.3.0"
    assert str(semver.Version.parse("1.0.0+build.5").next_version("major")) == "2.0.0"
    nxt = semver.Version.parse("1.0.0+build.5").next_version("patch")
    assert str(nxt) == "1.0.1"
    assert nxt.build is None


def test_cli_nextver_bumps_build_only_version():
    assert cmd_nextver(Namespace(version="1.2.3+build.5", part="patch")) == "1.2.4"
    assert cmd_nextver(Namespace(version="2.0.0+b1", part="major")) == "3.0.0"


def test_subclass_build_only_bump_preserves_type():
    class MyVersion(Version):
        pass

    nxt = MyVersion.parse("0.1.4+build.5").next_version("patch")
    assert isinstance(nxt, MyVersion)
    assert str(nxt) == "0.1.5"
