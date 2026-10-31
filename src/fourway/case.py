"""Benchmark cases: a seeded pair of changes with a known answer.

A case directory holds:

    case.toml   the label, the expected oracle finding, and each side's description
    a/          files change A adds or replaces on top of the base tree
    a.patch     a diff change A applies on top of the base tree, instead of or after a/
    b/, b.patch the same for change B
    oracle/     the hidden scenario that demonstrates the answer

The base tree is a directory in the corpus, or a pinned commit of a real
repository described in repos/<name>.toml. A pair mined from that repository's
history names its changes as upstream commits instead of carrying them, and
has no oracle: its clean label rests on the history, not on a scenario. Only
the base tree, the diffs, and the descriptions reach a generator.
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
    commits: tuple[str, str] | None = None  # upstream (from, to); the side is the diff between them


@dataclass(frozen=True)
class Upstream:
    """One commit of a real repository, pinned by its full SHA."""

    name: str
    url: str
    commit: str
    license: str


_SHA = re.compile(r"[0-9a-f]{40}")

# Keys a case's base table may set. The commit and the suite keys override
# repos/<name>.toml, because a layout can change between two commits.
_BASE_KEYS = frozenset({"repo", "commit", "tests", "pythonpath", "pytest_args"})


def _full_sha(sha: str, where: str) -> str:
    if not _SHA.fullmatch(sha):
        raise ValueError(f"{where}: commit must be a full 40-character SHA, got {sha!r}")
    return sha


def load_upstream(path: Path, base: dict | None = None) -> tuple[Upstream, Suite]:
    """Read repos/<name>.toml, with a case's ``base`` table laid over it."""
    base = base or {}
    if unknown := set(base) - _BASE_KEYS:
        raise ValueError(f"unknown keys in base: {sorted(unknown)}")
    meta = {**tomllib.loads(path.read_text()), **base}
    if "commit" not in meta:
        raise ValueError(f"{path.name} pins no commit, so each case must name one")
    suite = Suite(
        tests=meta.get("tests", "tests"),
        pythonpath=tuple(meta.get("pythonpath", ())),
        args=tuple(meta.get("pytest_args", ())),
    )
    return Upstream(path.stem, meta["url"], _full_sha(meta["commit"], path.name), meta["license"]), suite


def cache_dir() -> Path:
    return Path(os.environ.get("FOURWAY_CACHE") or Path.home() / ".cache" / "fourway")


def fetch(upstream: Upstream, *shas: str) -> Path:
    """Return the cache repository for ``upstream``, fetching any of ``shas`` it lacks, once."""
    cache = cache_dir() / "repos" / f"{upstream.name}.git"
    if not (cache / "HEAD").exists():
        cache.mkdir(parents=True, exist_ok=True)
        gitops.git(cache, "init", "--quiet", "--bare")
    missing = [sha for sha in dict.fromkeys(shas) if not gitops.has_commit(cache, sha)]
    if missing:
        gitops.git(cache, "fetch", "--quiet", "--depth", "1", upstream.url, *missing)
    for sha in missing:
        if not gitops.has_commit(cache, sha):
            raise gitops.GitError(f"{upstream.url} did not provide commit {sha}")
    return cache


def checkout_upstream(upstream: Upstream, dest: Path) -> Path:
    """Write the pinned commit's tree into ``dest``, fetching it into the cache once."""
    cache = fetch(upstream, upstream.commit)
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
    expect: str | None  # the finding the oracle must produce; None for a mined pair, which has no oracle
    conflict_class: str  # for measuring whether conflicts recur in classes
    a: Side
    b: Side
    suite: Suite = Suite()
    runtime: tuple[str, ...] = ("a", "b")  # mined pairs: sides that change code beyond docstrings and annotations
    assisted: tuple[str, ...] = ()  # mined pairs: sides whose pull request credits an AI assistant

    @property
    def oracle(self) -> Path:
        return self.path / "oracle"

    @property
    def mined(self) -> bool:
        """True for a pair of real changes from a repository's history, rather than seeded ones."""
        return self.a.commits is not None


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

    def side(name: str) -> Side:
        s = meta[name]
        patch = path / f"{name}.patch"
        commits = None
        if "from" in s or "to" in s:
            where = f"{path.name} [{name}]"
            commits = (_full_sha(s["from"], where), _full_sha(s["to"], where))
        return Side(
            Intent(s["title"], s["body"].strip()), path / name, tuple(s.get("deleted", ())),
            patch if patch.is_file() else None, commits,
        )

    a, b = side("a"), side("b")
    if isinstance(meta["base"], dict):
        base, suite = load_upstream(path.parents[1] / "repos" / f"{meta['base']['repo']}.toml", meta["base"])
    else:
        if a.commits or b.commits:
            raise ValueError(f"{path.name}: a side named by commits needs a repository base")
        base, suite = (path / meta["base"]).resolve(), Suite()
    expect = meta.get("expect")
    if expect is None:
        # Only history can stand in for an oracle, and only to say "clean".
        if not (a.commits and b.commits and meta["label"] == "clean"):
            raise ValueError(f"{path.name}: only a clean pair mined from history may omit expect and the oracle")
    elif expect not in classify.FINDINGS:
        raise ValueError(f"{path.name}: unknown expected finding {expect!r}")
    return Case(
        id=path.name,
        path=path,
        base=base,
        label=meta["label"],
        expect=expect,
        conflict_class=meta["class"],
        a=a,
        b=b,
        suite=suite,
        runtime=tuple(meta.get("runtime", ("a", "b"))),
        assisted=tuple(meta.get("assisted", ())),
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
        cache = fetch(case.base, *(sha for side in (case.a, case.b) for sha in side.commits or ()))
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
        if side.commits:
            # Replayed onto this base, not checked out: change B was made on
            # its own parent, which may already hold change A.
            patch = workdir / f"{name}.upstream.patch"
            patch.write_bytes(gitops.binary_diff(cache, *side.commits))
            gitops.git(repo, "apply", str(patch))
        for rel in side.deleted:
            (repo / rel).unlink()
        heads.append(gitops.commit_all(repo, side.intent.title))
    return Pair(repo, base, heads[0], heads[1])
