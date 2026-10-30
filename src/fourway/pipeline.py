"""Verify one pair: merge A and B, build the four trees, run scenarios four ways, classify."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from . import classify, gitops, runner


@dataclass(frozen=True)
class FourWay:
    shas: Mapping[str, str]  # variant -> commit SHA
    outcomes: Mapping[str, Mapping[str, str]]  # test id -> variant -> outcome
    findings: Mapping[str, str]  # test id -> finding
    verdict: str


def build_trees(repo: Path, base: str, a: str, b: str, workdir: Path) -> tuple[dict[str, str], dict[str, Path]]:
    """Merge A and B, then export all four commits. Raises MergeConflict."""
    shas = {"base": base, "a": a, "b": b, "ab": gitops.merge(repo, a, b)}
    trees = {variant: gitops.export(repo, sha, workdir / variant) for variant, sha in shas.items()}
    return shas, trees


def verify(
    repo: Path,
    base: str,
    a: str,
    b: str,
    scenarios: Mapping[str, str],
    workdir: Path,
    *,
    repeat: int = 1,
    timeout: float = 120.0,
) -> FourWay:
    shas, trees = build_trees(repo, base, a, b, workdir)
    outcomes: dict[str, dict[str, str]] = {}
    if scenarios:
        for tree in trees.values():
            runner.install_scenarios(tree, scenarios)
        outcomes = runner.run_four_way(
            trees, runner.SCENARIO_DIR, workdir / "reports", repeat=repeat, timeout=timeout
        )
    findings = {test: classify.classify(o) for test, o in outcomes.items()}
    return FourWay(shas, outcomes, findings, classify.verdict(findings.values()))
