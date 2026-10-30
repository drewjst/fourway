"""Turn one scenario's four outcomes into a finding, and a pair's findings into a verdict.

    base  A     B     A+B   finding
    any   pass  pass  fail  emergent        each change holds; only the combination breaks
    fail  pass  fail  fail  differential_a  A's new behavior is lost when B lands
    fail  fail  pass  fail  differential_b  B's new behavior is lost when A lands
    pass  fail  pass  fail  regression_a    A breaks it alone: an ordinary bug in A
    pass  pass  fail  fail  regression_b    B breaks it alone: an ordinary bug in B
    pass  fail  fail  fail  regression_ab   each breaks it alone
    fail  fail  fail  fail  inconclusive    the scenario never passes, so it proves nothing
    any   any   any   pass  ok

"pass" means the outcome "passed". "fail" on the merge means failed, error,
timeout, or missing; a skip on the merge is inconclusive, never a failure.
Only emergent and differential findings are conflicts. A regression is real
but belongs to one change, so its reproduction goes to that change's author.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

CONFLICTS = frozenset({"emergent", "differential_a", "differential_b"})
REGRESSIONS = frozenset({"regression_a", "regression_b", "regression_ab"})
FINDINGS = CONFLICTS | REGRESSIONS | {"ok", "inconclusive", "flaky"}

_MERGE_FAILURES = frozenset({"failed", "error", "timeout", "missing"})


def classify(outcomes: Mapping[str, str]) -> str:
    if "flaky" in outcomes.values():
        return "flaky"
    passed = {variant: outcome == "passed" for variant, outcome in outcomes.items()}
    if passed["ab"]:
        return "ok"
    if outcomes["ab"] not in _MERGE_FAILURES:
        return "inconclusive"
    if passed["a"] and passed["b"]:
        return "emergent"
    if passed["a"]:
        return "regression_b" if passed["base"] else "differential_a"
    if passed["b"]:
        return "regression_a" if passed["base"] else "differential_b"
    if passed["base"]:
        return "regression_ab"
    return "inconclusive"


def verdict(findings: Iterable[str]) -> str:
    """Return "conflict", "regression", "clean", or "unverified".

    "unverified" means no scenario produced a usable signal: there were none,
    or every one was inconclusive or flaky. It is never reported as clean.
    """
    found = set(findings)
    if found & CONFLICTS:
        return "conflict"
    if found & REGRESSIONS:
        return "regression"
    if "ok" in found:
        return "clean"
    return "unverified"
