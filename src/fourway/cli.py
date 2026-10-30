"""Command-line entry point."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path

from . import bench, gitops, ledger, pipeline
from .case import load_corpus
from .classify import CONFLICTS, REGRESSIONS
from .generators import BLIND, CONTROLS


def _check_corpus(args: argparse.Namespace) -> int:
    failed = 0
    for case in load_corpus(args.corpus):
        problems = bench.check_case(case)
        print(f"{'ok  ' if not problems else 'FAIL'}  {case.id}")
        for problem in problems:
            print(f"      {problem}")
        failed += bool(problems)
    return 1 if failed else 0


def _bench(args: argparse.Namespace) -> int:
    cases = load_corpus(args.corpus)
    results = bench.run(
        cases, args.generator, repeat=args.repeat, timeout=args.timeout, ledger_path=args.ledger
    )
    summary = bench.summarize(args.generator, results)
    print(bench.format_report(summary, results))
    if args.json:
        args.json.write_text(json.dumps({
            "summary": asdict(summary),
            "cases": [
                {"id": r.case.id, "label": r.case.label, "class": r.case.conflict_class,
                 "verdict": r.verdict, "findings": r.findings, "cost_usd": r.cost_usd,
                 "seconds": round(r.seconds, 2), "evidence": r.record["id"]}
                for r in results
            ],
        }, indent=2) + "\n")
    return 0


def _pair(args: argparse.Namespace) -> int:
    scenarios = {p.name: p.read_text() for p in sorted(args.scenarios.glob("test_*.py"))}
    if not scenarios:
        print(f"no test_*.py files in {args.scenarios}", file=sys.stderr)
        return 2
    shas = [gitops.resolve(args.repo, ref) for ref in (args.base, args.a, args.b)]
    with tempfile.TemporaryDirectory(prefix="fourway-pair-") as tmp:
        work = Path(tmp)
        clone = gitops.clone(args.repo, work / "repo")
        try:
            result = pipeline.verify(
                clone, *shas, scenarios, work / "run", repeat=args.repeat, timeout=args.timeout
            )
        except gitops.MergeConflict as e:
            print(e, file=sys.stderr)
            return 2
    rec = ledger.record(result, scenarios, generator="manual", repeat=args.repeat)
    if args.ledger:
        ledger.append(args.ledger, rec)
    for test, finding in sorted(result.findings.items()):
        outcomes = " ".join(f"{v}={o}" for v, o in result.outcomes[test].items())
        marker = "!!" if finding in CONFLICTS else "! " if finding in REGRESSIONS else "  "
        print(f"{marker} {finding:<15} {test}  [{outcomes}]")
    print(f"\nverdict  {result.verdict}\nevidence {rec['id']}")
    return 1 if result.verdict == "conflict" else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="fourway",
        description="Run scenarios on base, A, B, and A+B to catch changes that merge cleanly and break together.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--repeat", type=int, default=1, help="runs per tree; differing outcomes are flaky")
        p.add_argument("--timeout", type=float, default=120.0, help="seconds per pytest run")
        p.add_argument("--ledger", type=Path, help="append evidence records to this JSONL file")

    check = sub.add_parser("check-corpus", help="validate every benchmark case against its own answer key")
    check.add_argument("--corpus", type=Path, default=Path("corpus"))
    check.set_defaults(func=_check_corpus)

    run = sub.add_parser("bench", help="score a generator on the benchmark corpus")
    run.add_argument("--generator", required=True, choices=sorted({*BLIND, *CONTROLS}))
    run.add_argument("--corpus", type=Path, default=Path("corpus"))
    run.add_argument("--json", type=Path, help="also write results as JSON to this path")
    common(run)
    run.set_defaults(func=_bench)

    pair = sub.add_parser("pair", help="run a directory of scenario tests four ways on a git repo")
    pair.add_argument("--repo", type=Path, default=Path("."))
    pair.add_argument("--base", required=True)
    pair.add_argument("--a", required=True)
    pair.add_argument("--b", required=True)
    pair.add_argument("--scenarios", type=Path, required=True, help="directory of test_*.py files")
    common(pair)
    pair.set_defaults(func=_pair)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
