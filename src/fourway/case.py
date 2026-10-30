"""Benchmark cases: a seeded pair of changes with a known answer.

A case directory holds:

    case.toml   the label, the expected oracle finding, and each side's description
    a/          files change A adds or replaces on top of the base tree
    b/          the same for change B
    oracle/     the hidden scenario that demonstrates the answer

Only the base tree, the diffs, and the descriptions reach a generator.
"""

from __future__ import annotations

import shutil
import tomllib
from dataclasses import dataclass
from pathlib import Path

from . import classify, gitops

LABELS = ("conflict", "clean")

_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache")


@dataclass(frozen=True)
class Intent:
    title: str
    body: str


@dataclass(frozen=True)
class Side:
    intent: Intent
    overlay: Path
    deleted: tuple[str, ...]


@dataclass(frozen=True)
class Case:
    id: str
    path: Path
    base: Path
    label: str  # "conflict" or "clean": what a generator is scored against
    expect: str  # the finding the oracle must produce on this case
    conflict_class: str  # for measuring whether conflicts recur in classes
    a: Side
    b: Side

    @property
    def oracle(self) -> Path:
        return self.path / "oracle"


@dataclass(frozen=True)
class Pair:
    repo: Path
    base: str
    a: str
    b: str


def load_case(path: Path) -> Case:
    meta = tomllib.loads((path / "case.toml").read_text())
    if meta["label"] not in LABELS:
        raise ValueError(f"{path.name}: label must be one of {LABELS}")
    if meta["expect"] not in classify.FINDINGS:
        raise ValueError(f"{path.name}: unknown expected finding {meta['expect']!r}")

    def side(name: str) -> Side:
        s = meta[name]
        return Side(Intent(s["title"], s["body"].strip()), path / name, tuple(s.get("deleted", ())))

    return Case(
        id=path.name,
        path=path,
        base=(path / meta["base"]).resolve(),
        label=meta["label"],
        expect=meta["expect"],
        conflict_class=meta["class"],
        a=side("a"),
        b=side("b"),
    )


def load_corpus(root: Path) -> list[Case]:
    cases_dir = root / "cases"
    return [load_case(p) for p in sorted(cases_dir.iterdir()) if (p / "case.toml").exists()]


def _copy(src: Path, dest: Path) -> None:
    # shutil.copy, not the default copy2: copy2 keeps the source mtime. An
    # overlay file with the same size and mtime as the file it replaces looks
    # unchanged to git's stat cache, and `git add` silently skips it.
    shutil.copytree(src, dest, dirs_exist_ok=True, ignore=_IGNORE, copy_function=shutil.copy)


def materialize(case: Case, workdir: Path) -> Pair:
    """Build a git repo with the base commit on main and A and B on branches a and b."""
    repo = gitops.init(workdir / "repo")
    _copy(case.base, repo)
    base = gitops.commit_all(repo, "base")
    heads = []
    for name, side in (("a", case.a), ("b", case.b)):
        gitops.git(repo, "checkout", "--quiet", "-b", name, base)
        _copy(side.overlay, repo)
        for rel in side.deleted:
            (repo / rel).unlink()
        heads.append(gitops.commit_all(repo, side.intent.title))
    return Pair(repo, base, heads[0], heads[1])
