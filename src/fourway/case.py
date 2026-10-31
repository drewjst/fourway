"""Benchmark cases: a seeded pair of changes with a known answer.

A case directory holds:

    case.toml   the label, the expected oracle finding, and each side's description
    a/          files change A adds or replaces on top of the base tree
    a.patch     a diff change A applies on top of the base tree, instead of or after a/
    b/, b.patch the same for change B
    oracle/     the hidden scenario that demonstrates the answer

The base tree is a directory in the corpus, or a pinned commit of a real
repository described in repos/<name>.toml. Only the base tree, the diffs, and
the descriptions reach a generator.
"""

from __future__ import annotations

import os
import re
import shutil
import tomllib
from dataclasses import dataclass
from pathlib import Path

from . import classify, gitops
from .runner import Suite

LABELS = ("conflict", "clean")

_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", ".DS_Store")


@dataclass(frozen=True)
class Intent:
    title: str
    body: str


@dataclass(frozen=True)
class Side:
    intent: Intent
    overlay: Path
    deleted: tuple[str, ...]
    patch: Path | None = None


@dataclass(frozen=True)
class Upstream:
    """One commit of a real repository, pinned by its full SHA."""

    name: str
    url: str
    commit: str
    license: str


_SHA = re.compile(r"[0-9a-f]{40}")


def load_upstream(path: Path) -> tuple[Upstream, Suite]:
    meta = tomllib.loads(path.read_text())
    if not _SHA.fullmatch(meta["commit"]):
        raise ValueError(f"{path.name}: commit must be a full 40-character SHA, got {meta['commit']!r}")
    suite = Suite(
        tests=meta.get("tests", "tests"),
        pythonpath=tuple(meta.get("pythonpath", ())),
        args=tuple(meta.get("pytest_args", ())),
    )
    return Upstream(path.stem, meta["url"], meta["commit"], meta["license"]), suite


def cache_dir() -> Path:
    return Path(os.environ.get("FOURWAY_CACHE") or Path.home() / ".cache" / "fourway")


def checkout_upstream(upstream: Upstream, dest: Path) -> Path:
    """Write the pinned commit's tree into ``dest``, fetching it into the cache once."""
    cache = cache_dir() / "repos" / f"{upstream.name}.git"
    if not (cache / "HEAD").exists():
        cache.mkdir(parents=True, exist_ok=True)
        gitops.git(cache, "init", "--quiet", "--bare")
    if not gitops.has_commit(cache, upstream.commit):
        gitops.git(cache, "fetch", "--quiet", "--depth", "1", upstream.url, upstream.commit)
    if not gitops.has_commit(cache, upstream.commit):
        raise gitops.GitError(f"{upstream.url} did not provide commit {upstream.commit}")
    # The case repository is exported with `git archive`, which drops paths a
    # .gitattributes marks export-ignore and rewrites export-subst files.
    for name in gitops.git(cache, "ls-tree", "-r", "--name-only", upstream.commit).splitlines():
        if name.rsplit("/", 1)[-1] == ".gitattributes":
            rules = gitops.git(cache, "show", f"{upstream.commit}:{name}")
            if "export-ignore" in rules or "export-subst" in rules:
                raise ValueError(f"{upstream.name}: {name} uses export attributes; the exported trees would differ")
    return gitops.export(cache, upstream.commit, dest)


@dataclass(frozen=True)
class Case:
    id: str
    path: Path
    base: Path | Upstream
    label: str  # "conflict" or "clean": what a generator is scored against
    expect: str  # the finding the oracle must produce on this case
    conflict_class: str  # for measuring whether conflicts recur in classes
    a: Side
    b: Side
    suite: Suite = Suite()

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
        patch = path / f"{name}.patch"
        return Side(
            Intent(s["title"], s["body"].strip()), path / name, tuple(s.get("deleted", ())),
            patch if patch.is_file() else None,
        )

    if isinstance(meta["base"], dict):
        base, suite = load_upstream(path.parents[1] / "repos" / f"{meta['base']['repo']}.toml")
    else:
        base, suite = (path / meta["base"]).resolve(), Suite()
    return Case(
        id=path.name,
        path=path,
        base=base,
        label=meta["label"],
        expect=meta["expect"],
        conflict_class=meta["class"],
        a=side("a"),
        b=side("b"),
        suite=suite,
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
    if isinstance(case.base, Upstream):
        _copy(checkout_upstream(case.base, workdir / "upstream"), repo)
    else:
        _copy(case.base, repo)
    base = gitops.commit_all(repo, "base")
    heads = []
    for name, side in (("a", case.a), ("b", case.b)):
        gitops.git(repo, "checkout", "--quiet", "-b", name, base)
        if side.overlay.is_dir():
            _copy(side.overlay, repo)
        if side.patch:
            gitops.git(repo, "apply", str(side.patch.resolve()))
        for rel in side.deleted:
            (repo / rel).unlink()
        heads.append(gitops.commit_all(repo, side.intent.title))
    return Pair(repo, base, heads[0], heads[1])
