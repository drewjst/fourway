from typing import Optional

from semver import version as version_mod
from semver.version import Version, _cmp


def test_cmp_and_nat_cmp_have_int_return_annotations():
    assert _cmp.__annotations__.get("return") is int
    ann = Version._nat_cmp.__annotations__
    assert ann.get("return") is int
    assert ann.get("a") == Optional[str]
    assert ann.get("b") == Optional[str]
    assert hasattr(version_mod, "T_cmp")


def test_cmp_returns_ints_for_tuples_strings_ints():
    assert _cmp((1, 2, 3), (1, 2, 4)) == -1
    assert _cmp("b", "a") == 1
    assert _cmp(5, 5) == 0
    assert isinstance(Version._nat_cmp("rc.1", "rc.2"), int)
