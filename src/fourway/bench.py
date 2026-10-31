"""Check the corpus, and score a generator against it: recall, false positives, cost."""

from __future__ import annotations

import json
import math
import tempfile
import time
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from . import gitops, ledger, pipeline, runner
from .case import Case, materialize
from .generators import BLIND, CONTROLS, PairContext, Replay, Scenarios, read_oracle


@dataclass(frozen=True)
class CaseResult:
    case: Case
    scenarios: Scenarios
    verdict: str
    findings: dict[str, str]
    cost_usd: float
    seconds: float
    record: dict

    @property
    def detected(self) -> bool:
        return self.verdict == "conflict"


@dataclass(frozen=True)
class Summary:
    generator: str
    detected: int
    conflicts: int
    false_positives: int
    cleans: int
    cleans_verified: int  # clean pairs with a verdict; only these can show a false-positive rate
    unverified: int
    errors: int  # cases where the generator returned no scenarios because it failed
    fallbacks: int  # cases a fallback model served; their scenarios belong to another model
    total: int
    cost_usd: float
    models: tuple[str, ...]


# Generators whose scenarios this project wrote, or that write none.
TRUSTED = frozenset({"null", *CONTROLS})


def check_case(case: Case) -> list[str]:
    """Return what is wrong with a case. An empty list means the case is usable.

    A usable case merges cleanly, its existing test suite passes on all four
    trees (so ordinary CI on the merge cannot see the problem), and its oracle
    produces the expected finding and a verdict that matches the label. A pair
    mined from history has no oracle, so only the first two checks apply.
    """
    problems: list[str] = []
    oracle = read_oracle(case)
    if not oracle and case.expect is not None:
        return ["oracle/ has no test_*.py files"]
    with tempfile.TemporaryDirectory(prefix=f"fourway-check-{case.id}-") as tmp:
        work = Path(tmp)
        try:
            pair = materialize(case, work)
        except gitops.GitError as e:
            return [f"the case does not build: {e}"]
        try:
            _, trees = pipeline.build_trees(pair.repo, pair.base, pair.a, pair.b, work / "suite")
        except gitops.MergeConflict as e:
            return [str(e)]
        suite = runner.run_four_way(trees, case.suite.tests, work / "suite-reports", suite=case.suite)
        if not suite:
            problems.append(f"existing suite: no tests ran from {case.suite.tests!r}")
        elif not any(set(by_variant.values()) == {"passed"} for by_variant in suite.values()):
            problems.append("existing suite: no test passes on all four trees")
        for test, by_variant in suite.items():
            # A test that ran and failed the same way on all four trees fails in
            # this environment, for example on a newer Python, and says nothing
            # about A, B, or the merge. A file that fails to import still counts,
            # because it hides every test in it.
            if "::" in test and set(by_variant.values()) == {"failed"}:
                continue
            for variant, outcome in by_variant.items():
                # "missing" means the tree does not have the test, for example
                # because one side deleted it, and a real repository skips tests
                # whose optional dependencies are absent. Only a red test would
                # alert CI.
                if outcome not in ("passed", "missing", "skipped"):
                    problems.append(f"existing suite: {test} is {outcome} on {variant}")
        if case.expect is None:
            return problems
        result = pipeline.verify(
            pair.repo, pair.base, pair.a, pair.b, oracle, work / "oracle", suite=case.suite
        )
    if case.expect not in result.findings.values():
        problems.append(f"oracle findings {sorted(set(result.findings.values()))} lack {case.expect!r}")
    if (result.verdict == "conflict") != (case.label == "conflict"):
        problems.append(f"oracle verdict {result.verdict!r} contradicts label {case.label!r}")
    return problems


def run(
    cases: list[Case],
    generator: str,
    *,
    repeat: int = 1,
    timeout: float = 120.0,
    ledger_path: Path | None = None,
    options: dict | None = None,
) -> list[CaseResult]:
    """Run ``generator`` on every case.

    ``options`` go to a blind generator's constructor. For ``replay``, they hold
    ``root``, the ``--out`` directory of the run to replay.

    Model-written scenarios never run on a mined pair: its diffs and
    descriptions are third-party input, and decision 0002 keeps scenarios
    from such input out of the local runner until it is sandboxed.
    """
    if generator not in TRUSTED and (mined := [c.id for c in cases if c.mined]):
        raise ValueError(
            f"decision 0002: {generator!r} scenarios can't run on mined pairs until the runner is "
            f"sandboxed (issue #2); leave out {len(mined)} mined pair(s), for example with --seeded-only"
        )
    if generator in CONTROLS:
        control = CONTROLS[generator](cases)

        def source(case: Case, ctx: PairContext) -> Scenarios:
            return control.for_case(case)
    elif generator == Replay.name:
        replay = Replay(Path((options or {})["root"]))

        def source(case: Case, ctx: PairContext) -> Scenarios:
            return replay.for_case(case)
    elif generator in BLIND:
        blind = BLIND[generator](**(options or {}))

        def source(case: Case, ctx: PairContext) -> Scenarios:
            return blind.generate(ctx)
    else:
        raise ValueError(f"unknown generator {generator!r}")

    results = []
    for case in cases:
        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix=f"fourway-{case.id}-") as tmp:
            work = Path(tmp)
            pair = materialize(case, work)
            ctx = PairContext(
                base_tree=gitops.export(pair.repo, pair.base, work / "context"),
                diff_a=gitops.diff(pair.repo, pair.base, pair.a),
                diff_b=gitops.diff(pair.repo, pair.base, pair.b),
                intent_a=case.a.intent,
                intent_b=case.b.intent,
                pythonpath=case.suite.pythonpath,
            )
            scenarios = source(case, ctx)
            result = pipeline.verify(
                pair.repo, pair.base, pair.a, pair.b, scenarios.files, work / "run",
                repeat=repeat, timeout=timeout, suite=case.suite,
            )
        rec = ledger.record(
            result, scenarios.files, generator=generator, models=scenarios.models,
            config=scenarios.config, repeat=repeat,
        )
        if ledger_path:
            ledger.append(ledger_path, rec)
        results.append(CaseResult(
            case=case,
            scenarios=scenarios,
            verdict=result.verdict,
            findings=dict(result.findings),
            cost_usd=scenarios.cost_usd,
            seconds=time.monotonic() - started,
            record=rec,
        ))
    return results


def summarize(generator: str, results: list[CaseResult]) -> Summary:
    conflicts = [r for r in results if r.case.label == "conflict"]
    cleans = [r for r in results if r.case.label == "clean"]
    return Summary(
        generator=generator,
        detected=sum(r.detected for r in conflicts),
        conflicts=len(conflicts),
        false_positives=sum(r.detected for r in cleans),
        cleans=len(cleans),
        cleans_verified=sum(r.verdict != "unverified" for r in cleans),
        unverified=sum(r.verdict == "unverified" for r in results),
        errors=sum("error" in r.scenarios.notes for r in results),
        fallbacks=sum(bool(r.scenarios.notes.get("fallback")) for r in results),
        total=len(results),
        cost_usd=sum(r.cost_usd for r in results),
        models=tuple(sorted({m for r in results for m in r.scenarios.models})),
    )


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for k successes in n trials."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def _rate(k: int, n: int) -> str:
    lo, hi = wilson(k, n)
    return f"{k}/{n}  (95% CI {lo:.0%} to {hi:.0%})"


def false_positive_breakdown(results: list[CaseResult]) -> list[tuple[str, int, int]]:
    """Split false positives the ways corpus/README.md fixed before any run on mined pairs.

    Each group counts only verified pairs, as the headline rate does. Empty
    when the run has no mined pairs.
    """
    cleans = [r for r in results if r.case.label == "clean"]
    mined = [r for r in cleans if r.case.mined]
    if not mined:
        return []
    groups = {
        "seeded twins": [r for r in cleans if not r.case.mined],
        "mined, same file": [r for r in mined if r.case.conflict_class == "mined, same file"],
        "mined, other files": [r for r in mined if r.case.conflict_class == "mined, other files"],
        "mined, both sides change code": [r for r in mined if set(r.case.runtime) == {"a", "b"}],
        "mined, no side AI-credited": [r for r in mined if not r.case.assisted],
    }
    return [
        (name, sum(r.detected for r in rs), sum(r.verdict != "unverified" for r in rs))
        for name, rs in groups.items()
    ]


def format_report(summary: Summary, results: list[CaseResult]) -> str:
    rows = [("case", "label", "expect", "verdict", "findings", "secs")]
    for r in results:
        counts = Counter(r.findings.values())
        findings = ", ".join(f"{k} ({v})" for k, v in sorted(counts.items())) or "-"
        rows.append((r.case.id, r.case.label, r.case.expect or "-", r.verdict, findings, f"{r.seconds:.1f}"))
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    lines = ["  ".join(cell.ljust(w) for cell, w in zip(row, widths)).rstrip() for row in rows]
    per_pair = summary.cost_usd / summary.total if summary.total else 0.0
    lines += [
        "",
        f"generator        {summary.generator} {' '.join(summary.models)}".rstrip(),
        f"recall           {_rate(summary.detected, summary.conflicts)}",
        # An unverified clean pair shows nothing either way. Counting it as a pass
        # would give a generator that writes no scenarios a perfect rate.
        f"false positives  {_rate(summary.false_positives, summary.cleans_verified)}"
        + (f"; {left_out} unverified clean pair(s) left out"
           if (left_out := summary.cleans - summary.cleans_verified) else ""),
        *(f"  {name:<31}{_rate(k, n)}" for name, k, n in false_positive_breakdown(results)),
        f"unverified       {summary.unverified}/{summary.total}",
        f"generator errors {summary.errors}/{summary.total}",
        f"cost             ${summary.cost_usd:.2f} total, ${per_pair:.2f} per pair",
    ]
    if summary.fallbacks:
        lines.append(
            f"WARNING          a fallback model served {summary.fallbacks} case(s); "
            "those scenarios are not the named model's, and their cost is a lower bound"
        )
    return "\n".join(lines)


def save(results: list[CaseResult], summary: Summary, out: Path) -> None:
    """Write each case's scenarios and outcomes under ``out`` so misses can be read, not guessed at."""
    out.mkdir(parents=True, exist_ok=True)
    for r in results:
        case_dir = out / r.case.id
        (case_dir / "scenarios").mkdir(parents=True, exist_ok=True)
        for name, source in r.scenarios.files.items():
            (case_dir / "scenarios" / name).write_text(source)
        (case_dir / "result.json").write_text(json.dumps({
            "label": r.case.label,
            "expect": r.case.expect,
            "verdict": r.verdict,
            "notes": r.scenarios.notes,
            "evidence": r.record,
        }, indent=2, default=str) + "\n")
    (out / "summary.json").write_text(json.dumps({
        "summary": asdict(summary),
        "cases": [
            {"id": r.case.id, "label": r.case.label, "class": r.case.conflict_class,
             "mined": r.case.mined, "runtime": list(r.case.runtime), "assisted": list(r.case.assisted),
             "verdict": r.verdict, "findings": r.findings, "cost_usd": r.cost_usd,
             "seconds": round(r.seconds, 2), "evidence": r.record["id"]}
            for r in results
        ],
    }, indent=2) + "\n")
