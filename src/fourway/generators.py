"""Scenario generators.

A blind generator sees only a PairContext: the base tree, the two diffs, and
the two change descriptions. It never sees a case id, a label, or an oracle,
because the context has no field that could carry them.

Controls read the corpus answer key. They exist only to show the benchmark
can tell a right scenario set from a wrong one: the oracle should find every
seeded conflict, and the deranged oracle (right kind of scenario, wrong pair)
should find almost none.

Replay reads back the scenarios an earlier run saved, so a change to the
runner or the classifier can be scored on the same generated files for free.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from .case import Case, Intent


@dataclass(frozen=True)
class PairContext:
    base_tree: Path
    diff_a: str
    diff_b: str
    intent_a: Intent
    intent_b: Intent


@dataclass(frozen=True)
class Scenarios:
    files: dict[str, str]
    models: tuple[str, ...] = ()
    cost_usd: float = 0.0
    notes: dict = field(default_factory=dict)  # per-run detail: stop reason, tokens, errors
    config: dict = field(default_factory=dict)  # what produced the files: model, effort, prompt digest


class Generator(Protocol):
    name: str

    def generate(self, ctx: PairContext) -> Scenarios: ...


class Control(Protocol):
    name: str

    def for_case(self, case: Case) -> Scenarios: ...


class Null:
    """Writes no scenarios. Every pair comes out unverified."""

    name = "null"

    def generate(self, ctx: PairContext) -> Scenarios:
        return Scenarios({})


def read_oracle(case: Case) -> dict[str, str]:
    return {p.name: p.read_text() for p in sorted(case.oracle.glob("test_*.py"))}


class Oracle:
    name = "oracle"

    def for_case(self, case: Case) -> Scenarios:
        return Scenarios(read_oracle(case))


class Deranged:
    """Gives each case the oracle of the next case in id order."""

    name = "deranged"

    def __init__(self, cases: list[Case]):
        if len(cases) < 2:
            raise ValueError("a derangement needs at least two cases")
        ordered = sorted(cases, key=lambda c: c.id)
        self._donor = {c.id: ordered[(i + 1) % len(ordered)] for i, c in enumerate(ordered)}

    def for_case(self, case: Case) -> Scenarios:
        return Scenarios(read_oracle(self._donor[case.id]))


class Replay:
    """Serves the scenarios an earlier ``bench --out`` run saved for each case.

    The generator's output stays fixed, so a score that changes on replay
    changed because of the runner or the classifier, not the model.
    """

    name = "replay"

    def __init__(self, root: Path):
        if not (root / "summary.json").is_file():
            raise ValueError(f"{root} has no summary.json; pass a directory written by bench --out")
        self.root = root

    def for_case(self, case: Case) -> Scenarios:
        case_dir = self.root / case.id
        if not (case_dir / "result.json").is_file():
            return Scenarios({}, notes={"replayed_from": str(self.root), "error": "case missing from the earlier run"})
        earlier = json.loads((case_dir / "result.json").read_text())
        generator = earlier["evidence"]["generator"]
        return Scenarios(
            {p.name: p.read_text() for p in sorted((case_dir / "scenarios").glob("test_*.py"))},
            models=tuple(generator["models"]),
            notes={**earlier["notes"], "replayed_from": str(self.root)},
            config=generator["config"] or {},
        )


def _claude(**options) -> Generator:
    from .claude import ClaudeGenerator

    return ClaudeGenerator(**options)


BLIND: dict[str, Callable[..., Generator]] = {"null": lambda **options: Null(), "claude": _claude}
CONTROLS: dict[str, Callable[[list[Case]], Control]] = {
    "oracle": lambda cases: Oracle(),
    "deranged": Deranged,
}
