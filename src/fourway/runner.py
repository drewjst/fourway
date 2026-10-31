"""Run tests against the four trees of a pair and collect one outcome per test per tree.

Phase 0 runs pytest as a local subprocess. That is safe only for scenarios
generated from diffs we wrote ourselves; see docs/decisions/0002.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

VARIANTS = ("base", "a", "b", "ab")
SCENARIO_DIR = "fourway_scenarios"

_SCENARIO_NAME = re.compile(r"test_[A-Za-z0-9_]+\.py")


@dataclass(frozen=True)
class RunReport:
    """What one pytest run on one tree produced."""

    outcomes: Mapping[str, str]
    collect_errors: frozenset[str]
    crashed: str | None = None  # "timeout" or "error" when pytest wrote no report

    def outcome(self, test_id: str) -> str:
        if test_id in self.outcomes:
            return self.outcomes[test_id]
        if self.crashed:
            return self.crashed
        if test_id.split("::")[0] in self.collect_errors:
            return "error"
        return "missing"


@dataclass(frozen=True)
class Suite:
    """How pytest runs in a tree of one repository.

    ``tests`` holds the repository's own test suite. ``pythonpath`` lists
    directories put on sys.path after the tree root, such as ``src`` for a
    src-layout package. ``args`` are extra pytest flags for every run in the
    repository, scenario runs included, for example to drop an ``addopts``
    that needs a plugin fourway does not install.
    """

    tests: str = "tests"
    pythonpath: tuple[str, ...] = ()
    args: tuple[str, ...] = ()


def install_scenarios(tree: Path, scenarios: Mapping[str, str]) -> None:
    target = tree / SCENARIO_DIR
    target.mkdir()
    for name, source in scenarios.items():
        if not _SCENARIO_NAME.fullmatch(name):
            raise ValueError(f"scenario file name must match test_*.py with no path: {name!r}")
        (target / name).write_text(source)


def run_pytest(tree: Path, target: str, report: Path, timeout: float, suite: Suite = Suite()) -> RunReport:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "PYTHONPATH": os.pathsep.join(str(tree / p) for p in (".", *suite.pythonpath)),
        "PYTHONHASHSEED": "0",
        "PYTHONDONTWRITEBYTECODE": "1",
        "FOURWAY_REPORT": str(report),
    }
    cmd = [
        sys.executable, "-m", "pytest", target, "-q",
        "-p", "no:cacheprovider",
        "-p", "fourway.pytest_plugin",
        "--import-mode=importlib",
        # By default one file that fails to import stops the session, and every
        # other scenario reads as "missing" on that tree. A scenario that imports
        # a module only one side adds does exactly that on the other trees.
        "--continue-on-collection-errors",
        *suite.args,
    ]
    try:
        subprocess.run(cmd, cwd=tree, env=env, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return RunReport({}, frozenset(), crashed="timeout")
    if not report.exists():
        return RunReport({}, frozenset(), crashed="error")
    data = json.loads(report.read_text())
    return RunReport(data["tests"], frozenset(data["collect_errors"]))


def run_four_way(
    trees: Mapping[str, Path],
    target: str,
    reports_dir: Path,
    *,
    repeat: int = 1,
    timeout: float = 120.0,
    suite: Suite = Suite(),
) -> dict[str, dict[str, str]]:
    """Run ``target`` on each tree ``repeat`` times. Return {test id: {variant: outcome}}.

    A test whose outcome differs between repeats on the same tree is "flaky".
    Trees run in parallel; repeats on one tree run in sequence so a scenario
    that writes files cannot race itself.
    """
    reports_dir.mkdir(parents=True, exist_ok=True)

    def run_variant(variant: str) -> list[RunReport]:
        return [
            run_pytest(trees[variant], target, reports_dir / f"{variant}-{i}.json", timeout, suite)
            for i in range(repeat)
        ]

    with ThreadPoolExecutor(max_workers=len(VARIANTS)) as pool:
        runs = dict(zip(VARIANTS, pool.map(run_variant, VARIANTS)))

    test_ids: set[str] = set()
    for reports in runs.values():
        for r in reports:
            test_ids.update(r.outcomes)
    # A scenario file that fails to import everywhere has no test ids. Keep it as
    # one entry so it counts as a broken scenario instead of vanishing.
    seen_files = {t.split("::")[0] for t in test_ids}
    for reports in runs.values():
        for r in reports:
            test_ids.update(f for f in r.collect_errors if f and f not in seen_files)

    results: dict[str, dict[str, str]] = {}
    for test_id in sorted(test_ids):
        results[test_id] = {}
        for variant, reports in runs.items():
            seen = {r.outcome(test_id) for r in reports}
            results[test_id][variant] = seen.pop() if len(seen) == 1 else "flaky"
    return results
