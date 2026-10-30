"""The classification table decides who gets a reproduction, so each row states why."""

import pytest

from fourway.classify import classify, verdict

P, F, E, S = "passed", "failed", "error", "skipped"

ROWS = [
    # base, a, b, ab, finding, why
    (P, P, P, F, "emergent",
     "each change keeps the property and only the combination breaks it: the double charge"),
    (F, P, P, F, "emergent",
     "a property neither base nor the merge has, but each side has alone, is still lost by combining"),
    (E, P, E, F, "differential_a",
     "A's new behavior works on A and is gone after B lands, so B broke A's intent"),
    (E, E, P, F, "differential_b",
     "the mirror case: A broke B's intent"),
    (P, F, P, F, "regression_a",
     "A breaks base behavior on its own; blaming the pair would send B's author a bug that isn't theirs"),
    (P, P, F, F, "regression_b",
     "the mirror case: an ordinary bug in B"),
    (P, F, F, F, "regression_ab",
     "both sides break it alone; neither is an interaction"),
    (F, F, F, F, "inconclusive",
     "a scenario that never passes proves nothing about the merge"),
    (F, F, F, P, "ok",
     "a scenario that needs both changes and passes on the merge is not a conflict"),
    (P, P, P, S, "inconclusive",
     "a skip on the merge is not a failure; counting it would block merges on pytest.skip"),
    (P, P, P, "timeout", "emergent",
     "a merge that hangs where neither side does is a real interaction"),
]


@pytest.mark.parametrize(
    "base,a,b,ab,finding", [row[:5] for row in ROWS], ids=[row[5] for row in ROWS]
)
def test_four_outcomes_map_to_a_finding(base, a, b, ab, finding):
    assert classify({"base": base, "a": a, "b": b, "ab": ab}) == finding


def test_a_flaky_tree_overrides_everything():
    """An outcome that changes between runs cannot support a conflict claim, whatever the other trees say."""
    assert classify({"base": P, "a": P, "b": P, "ab": "flaky"}) == "flaky"
    assert classify({"base": "flaky", "a": P, "b": P, "ab": F}) == "flaky"


def test_any_conflict_makes_the_pair_conflict():
    assert verdict(["ok", "inconclusive", "emergent"]) == "conflict"


def test_a_regression_without_a_conflict_is_reported_as_a_regression():
    assert verdict(["ok", "regression_a"]) == "regression"


def test_no_usable_signal_is_unverified_not_clean():
    """An agent asking "was this combination verified?" must not hear yes when nothing ran."""
    assert verdict([]) == "unverified"
    assert verdict(["inconclusive", "flaky"]) == "unverified"


def test_one_passing_scenario_makes_the_pair_clean():
    assert verdict(["ok", "inconclusive"]) == "clean"
