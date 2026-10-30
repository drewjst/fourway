"""Loaded into each pytest run under test. Writes one outcome per test to $FOURWAY_REPORT.

The runner reads this file instead of pytest's exit code because a single exit
code cannot say which scenario failed on which tree.
"""

from __future__ import annotations

import json
import os

_outcomes: dict[str, str] = {}
_collect_errors: list[str] = []


def pytest_collectreport(report):
    if report.failed:
        _collect_errors.append(report.nodeid)


def pytest_runtest_logreport(report):
    # Reports arrive in order: setup, call (only if setup passed), teardown.
    if report.when == "call":
        _outcomes[report.nodeid] = report.outcome
    elif report.failed:
        _outcomes[report.nodeid] = "error"
    elif report.skipped:
        _outcomes[report.nodeid] = "skipped"


def pytest_sessionfinish(session, exitstatus):
    path = os.environ.get("FOURWAY_REPORT")
    if not path:
        return
    with open(path, "w") as f:
        json.dump(
            {"tests": _outcomes, "collect_errors": _collect_errors, "exitstatus": int(exitstatus)},
            f,
        )
