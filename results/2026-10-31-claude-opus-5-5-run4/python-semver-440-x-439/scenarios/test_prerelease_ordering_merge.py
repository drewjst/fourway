import warnings

import pytest

import semver
from semver import Version
from semver import cli


CHAIN = [
    "1.0.0-alpha",
    "1.0.0-alpha.1",
    "1.0.0-alpha.beta",
    "1.0.0-beta",
    "1.0.0-beta.2",
    "1.0.0-beta.11",
    "1.0.0-rc.1",
    "1.0.0",
]


def test_prerelease_chain_ordering_via_version_and_nat_cmp():
    for low, high in zip(CHAIN[:-1], CHAIN[1:]):
        assert Version.parse(low).compare(high) == -1, (low, high)
        assert Version.parse(high).compare(low) == 1, (high, low)
    # direct natural comparison of prerelease tags
    assert Version._nat_cmp("rc.2", "rc.10") == -1
    assert Version._nat_cmp("2", "rc") == -1
    assert Version._nat_cmp("rc", "2") == 1
    assert Version._nat_cmp("rc.2.1", "rc.2") == 1
    assert Version._nat_cmp(None, None) == 0
    assert Version._nat_cmp("Rc10", "rc10") == -1
    # Leading-digit mixed identifiers are strings, not ints
    assert Version._nat_cmp("0foo.1", "0foo.1") == 0


def test_deprecated_and_cli_compare_use_prerelease_ordering(capsys):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        assert semver.compare("1.0.0-beta.2", "1.0.0-beta.11") == -1
        assert semver.min_ver("1.2.3-rc.2", "1.2.3-rc.10") == "1.2.3-rc.2"
        assert semver.max_ver("1.2.3-2", "1.2.3-rc") == "1.2.3-rc"
    rc = cli.main(["compare", "1.0.0-alpha.beta", "1.0.0-alpha.1"])
    assert rc == 0
    assert capsys.readouterr().out.strip() == "1"


def test_deprecated_compare_still_warns_and_returns_value():
    with pytest.warns(PendingDeprecationWarning):
        assert semver.compare("1.0.0-rc.1", "1.0.0") == -1
