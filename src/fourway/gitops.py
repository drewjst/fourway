"""Git plumbing for the four trees of a pair: base, A, B, and the merge of A and B.

Every command runs with a fixed identity, fixed dates, and no user or system
config, so the same inputs produce the same commit SHAs. The ledger keys
evidence on those SHAs.
"""

from __future__ import annotations

import io
import os
import subprocess
import tarfile
from pathlib import Path

_ENV = {
    "GIT_AUTHOR_NAME": "fourway",
    "GIT_AUTHOR_EMAIL": "fourway@localhost",
    "GIT_AUTHOR_DATE": "946684800 +0000",
    "GIT_COMMITTER_NAME": "fourway",
    "GIT_COMMITTER_EMAIL": "fourway@localhost",
    "GIT_COMMITTER_DATE": "946684800 +0000",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
}
_CONFIG = (
    "-c", "init.defaultBranch=main",
    "-c", "commit.gpgsign=false",
    "-c", f"core.hooksPath={os.devnull}",
    "-c", "core.autocrlf=false",
)


class GitError(RuntimeError):
    pass


class MergeConflict(RuntimeError):
    """A and B conflict textually. Fourway verifies only pairs that merge cleanly."""


def _run(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    proc = subprocess.run(
        ["git", *_CONFIG, "-C", str(repo), *args],
        capture_output=True,
        env={**os.environ, **_ENV},
    )
    if check and proc.returncode != 0:
        detail = proc.stderr.decode(errors="replace").strip()
        raise GitError(f"git {' '.join(args)}: {detail}")
    return proc


def git(repo: Path, *args: str) -> str:
    return _run(repo, *args).stdout.decode().strip()


def init(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "--quiet")
    return path


def clone(src: Path, dest: Path) -> Path:
    """Clone without a checkout, sharing objects, so merges never touch the source repo."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    _run(dest.parent, "clone", "--quiet", "--no-checkout", "--shared", str(src.resolve()), str(dest))
    return dest


def commit_all(repo: Path, message: str) -> str:
    git(repo, "add", "--all")
    git(repo, "commit", "--quiet", "--allow-empty", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def resolve(repo: Path, ref: str) -> str:
    return git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}")


def merge(repo: Path, a: str, b: str) -> str:
    """Return the SHA of a merge commit of A and B, or raise MergeConflict."""
    proc = _run(repo, "merge-tree", "--write-tree", "--name-only", a, b, check=False)
    out = proc.stdout.decode()
    if proc.returncode == 1:
        files = [line for line in out.split("\n\n")[0].splitlines()[1:] if line]
        raise MergeConflict("A and B conflict textually in: " + ", ".join(files))
    if proc.returncode != 0:
        raise GitError(f"git merge-tree: {proc.stderr.decode(errors='replace').strip()}")
    tree = out.splitlines()[0]
    return git(repo, "commit-tree", tree, "-p", a, "-p", b, "-m", "fourway: merge A and B")


def export(repo: Path, sha: str, dest: Path) -> Path:
    """Write the tree at ``sha`` into ``dest`` with no .git directory, so tests cannot reach the repo."""
    data = _run(repo, "archive", "--format=tar", sha).stdout
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        tar.extractall(dest, filter="data")
    return dest


def diff(repo: Path, old: str, new: str) -> str:
    return _run(repo, "diff", "--no-color", "--no-ext-diff", old, new).stdout.decode()
