"""Run tests against the four trees of a pair and collect one outcome per test per tree.

pytest runs either as a local subprocess or, through the fourway-sandbox
binary, in a container with no network, no credentials, and a read-only tree.
The local runner is safe only for scenarios generated from diffs we wrote
ourselves; see docs/decisions/0002 and 0003.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

VARIANTS = ("base", "a", "b", "ab")
SCENARIO_DIR = "fourway_scenarios"

_SCENARIO_NAME = re.compile(r"test_[A-Za-z0-9_]+\.py")

SANDBOX_IMAGE = "fourway-sandbox"
# Built by: go build -C sandbox -o bin/fourway-sandbox .
_CHECKOUT_SANDBOX = Path(__file__).resolve().parents[2] / "sandbox" / "bin" / "fourway-sandbox"


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


class SandboxError(RuntimeError):
    """The sandbox itself failed. Never a session outcome: a broken sandbox must not read as broken scenarios."""


@dataclass(frozen=True)
class Sandbox:
    """Runs each pytest session in a container through the fourway-sandbox binary.

    ``image`` is an image ID, resolved once, so every session in a run uses
    the same image and the evidence ledger can name it.
    """

    binary: str
    image: str

    @classmethod
    def resolve(cls, image: str = SANDBOX_IMAGE) -> Sandbox:
        binary = shutil.which("fourway-sandbox") or (str(_CHECKOUT_SANDBOX) if _CHECKOUT_SANDBOX.exists() else None)
        if binary is None:
            raise SandboxError("fourway-sandbox not found; build it with: go build -C sandbox -o bin/fourway-sandbox .")
        proc = subprocess.run([binary, "image", image], capture_output=True, text=True)
        if proc.returncode:
            raise SandboxError(proc.stderr.strip())
        return cls(binary, proc.stdout.strip())

    def run(self, tree: Path, args: list[str], report: Path, timeout: float, suite: Suite) -> RunReport:
        cmd = [self.binary, "run", "--image", self.image, "--tree", str(tree), "--timeout", f"{timeout}s"]
        for p in suite.pythonpath:
            cmd += ["--pythonpath", p]
        try:
            # The binary enforces the timeout; this one only catches a hung binary.
            proc = subprocess.run([*cmd, "--", *args], capture_output=True, text=True, timeout=timeout + 60)
        except subprocess.TimeoutExpired as e:
            raise SandboxError(f"fourway-sandbox did not return within {timeout + 60:.0f} s") from e
        if proc.returncode:
            raise SandboxError(proc.stderr.strip() or f"fourway-sandbox exited {proc.returncode}")
        result = json.loads(proc.stdout)
        if result["image"] != self.image:
            raise SandboxError(f"fourway-sandbox ran {result['image']}, not {self.image}")
        if result.get("crashed"):
            return RunReport({}, frozenset(), crashed=result["crashed"])
        # Keep the same report files a local run leaves behind.
        report.write_text(json.dumps(result["report"]))
        return RunReport(result["report"]["tests"], frozenset(result["report"]["collect_errors"]))


def pytest_args(target: str, suite: Suite = Suite()) -> list[str]:
    """Arguments to python -m pytest, the same for a local and a sandboxed run."""
    return [
        target, "-q",
        "-p", "no:cacheprovider",
        "-p", "fourway.pytest_plugin",
        "--import-mode=importlib",
        # By default one file that fails to import stops the session, and every
        # other scenario reads as "missing" on that tree. A scenario that imports
        # a module only one side adds does exactly that on the other trees.
        "--continue-on-collection-errors",
        *suite.args,
    ]


def run_pytest(
    tree: Path, target: str, report: Path, timeout: float, suite: Suite = Suite(), sandbox: Sandbox | None = None
) -> RunReport:
    if sandbox is not None:
        return sandbox.run(tree, pytest_args(target, suite), report, timeout, suite)
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "PYTHONPATH": os.pathsep.join(str(tree / p) for p in (".", *suite.pythonpath)),
        "PYTHONHASHSEED": "0",
        "PYTHONDONTWRITEBYTECODE": "1",
        "FOURWAY_REPORT": str(report),
    }
    cmd = [sys.executable, "-m", "pytest", *pytest_args(target, suite)]
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
    sandbox: Sandbox | None = None,
) -> dict[str, dict[str, str]]:
    """Run ``target`` on each tree ``repeat`` times. Return {test id: {variant: outcome}}.

    A test whose outcome differs between repeats on the same tree is "flaky".
    Trees run in parallel; repeats on one tree run in sequence so a scenario
    that writes files cannot race itself.
    """
    reports_dir.mkdir(parents=True, exist_ok=True)

    def run_variant(variant: str) -> list[RunReport]:
        return [
            run_pytest(trees[variant], target, reports_dir / f"{variant}-{i}.json", timeout, suite, sandbox)
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
