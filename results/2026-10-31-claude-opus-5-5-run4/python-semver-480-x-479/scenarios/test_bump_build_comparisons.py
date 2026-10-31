import pytest

from semver import Version


class VPrefixed(Version):
    def __str__(self):
        return "v" + super().__str__()


def test_digitless_build_raised_and_still_comparable_to_collections():
    v = Version.parse("1.2.3-rc.1+alpha")
    bumped = v.bump_build()
    assert bumped.build == "alpha.0"
    assert str(bumped) == "1.2.3-rc.1+alpha.0"
    assert bumped.to_tuple() == (1, 2, 3, "rc.1", "alpha.0")
    # comparisons against well-formed collections still work
    assert bumped == (1, 2, 3, "rc.1", "alpha.0")
    assert bumped == [1, 2, 3, "rc.1"]
    assert bumped == {"major": 1, "minor": 2, "patch": 3, "prerelease": "rc.1", "build": "alpha.0"}
    assert bumped < (1, 2, 3)
    assert bumped.bump_build().build == "alpha.1"


def test_subclass_digitless_build_bump_and_tuple_compare():
    v = VPrefixed(1, 2, 3, None, "exp.sha")
    bumped = v.bump_build()
    assert type(bumped) is VPrefixed
    assert bumped.build == "exp.sha.0"
    assert str(bumped) == "v1.2.3+exp.sha.0"
    assert bumped == (1, 2, 3)
    assert bumped == {"major": 1, "minor": 2, "patch": 3, "build": "exp.sha.0"}
    assert (2, 0, 0) > bumped
