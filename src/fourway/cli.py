"""Command-line entry point."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from . import bench, gitops, ledger, pipeline
from .case import load_corpus
from .classify import CONFLICTS, REGRESSIONS
from .generators import BLIND, CONTROLS, Replay

# The corpus ships with the repository, not the package; find it from a checkout.
_REPO_CORPUS = Path(__file__).resolve().parents[2] / "corpus"
DEFAULT_CORPUS = _REPO_CORPUS if _REPO_CORPUS.is_dir() else Path("corpus")


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
    options = {k: v for k, v in (("model", args.model), ("effort", args.effort)) if v}
    if options and args.generator != "claude":
        print("--model and --effort apply only to --generator claude", file=sys.stderr)
        return 2
    if (args.replay_from is None) == (args.generator == Replay.name):
        print("--from is required with --generator replay and applies only to it", file=sys.stderr)
        return 2
    if args.replay_from:
        options = {"root": args.replay_from}
    results = bench.run(
        cases, args.generator, repeat=args.repeat, timeout=args.timeout,
        ledger_path=args.ledger, options=options,
    )
    summary = bench.summarize(args.generator, results)
    print(bench.format_report(summary, results))
    if args.out:
        bench.save(results, summary, args.out)
        print(f"\nscenarios and outcomes saved to {args.out}")
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
    check.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    check.set_defaults(func=_check_corpus)

    run = sub.add_parser("bench", help="score a generator on the benchmark corpus")
    run.add_argument("--generator", required=True, choices=sorted({*BLIND, *CONTROLS, Replay.name}))
    run.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    run.add_argument("--out", type=Path, help="save each case's scenarios and outcomes under this directory")
    run.add_argument("--model", help="Claude model id (generator claude only; default claude-opus-5-5)")
    run.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"],
                     help="Claude effort level (generator claude only; default high)")
    run.add_argument("--from", dest="replay_from", type=Path,
                     help="--out directory of an earlier run (generator replay only)")
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
