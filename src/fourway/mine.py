"""Mine clean pairs from a repository's merged pull requests.

A mined pair is two pull requests that were open at the same time and landed
one after the other on the default branch, each changing the package's Python
code. The base is the branch just before the first one landed. Change A is
the first landing's diff, and change B is the second landing's diff replayed
onto that base.

The label is clean because the project shipped the merge and never reverted
either change. That is an assumption about real history, not a verified fact:
a latent conflict nobody noticed would still be labeled clean. The rule is
fixed here, before any generator runs on the pairs, so the selection can be
rerun and audited. corpus/README.md states it in prose.

Mining reads history and never runs upstream code. ``fourway check-corpus
--prune-mined`` runs each candidate's suite on the four trees and drops the
pairs that fail.
"""

from __future__ import annotations

import ast
import json
import re
import shutil
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path

from . import gitops
from .case import checkout_upstream, load_case
from .claude import TreeTooLarge, render_tree


@dataclass(frozen=True)
class Landing:
    """A merged pull request as one first-parent commit on the default branch."""

    number: int
    url: str
    title: str
    body: str
    opened: str  # ISO 8601 in UTC, as GitHub reports it, so strings compare in time order
    merged: str
    parent: str
    commit: str
    code: tuple[str, ...]  # the package's Python files it changes, tests excluded


def is_bot(pr: dict) -> bool:
    return pr.get("user_type") == "Bot" or pr["user"].endswith(("[bot]", "-bot"))


def is_code(path: str, packages: tuple[str, ...]) -> bool:
    parts = path.split("/")
    return (
        path.endswith(".py") and path.startswith(packages)
        and not {"tests", "test"} & set(parts[:-1]) and not parts[-1].startswith("test_")
    )


def landings(repo: Path, prs: list[dict], packages: tuple[str, ...], cutoff: str, branch: str = "HEAD") -> list[Landing]:
    """Return human pull requests that landed before ``cutoff`` as one commit, in landing order.

    A merge commit or a squash commit holds the whole pull request. A rebase
    merge spreads it over commits the history can't delimit, so it's skipped.
    """
    order = gitops.git(repo, "rev-list", "--first-parent", "--reverse", branch).split()
    position = {sha: i for i, sha in enumerate(order)}
    found = []
    for pr in prs:
        sha = pr["merge_commit_sha"]
        if not pr["merged_at"] or pr["merged_at"] >= cutoff or is_bot(pr) or sha not in position:
            continue
        parents = gitops.git(repo, "rev-list", "--parents", "-n1", sha).split()[1:]
        subject = gitops.git(repo, "log", "-1", "--format=%s", sha)
        if len(parents) != 2 and not (len(parents) == 1 and subject.endswith(f"(#{pr['number']})")):
            continue
        # --no-renames: rename detection reads file contents, which a blobless clone lacks.
        files = gitops.git(repo, "diff", "--name-only", "--no-renames", parents[0], sha).splitlines()
        found.append((position[sha], Landing(
            number=pr["number"], url=pr["html_url"], title=pr["title"], body=pr.get("body") or "",
            opened=pr["created_at"], merged=pr["merged_at"], parent=parents[0], commit=sha,
            code=tuple(f for f in files if is_code(f, packages)),
        )))
    return [landing for _, landing in sorted(found, key=lambda item: item[0])]


def pairs(landed: list[Landing]) -> list[tuple[Landing, Landing]]:
    """Pair each code landing with the next one if that pull request was opened before it merged.

    A pull request joins at most one pair, so no two pairs share a change and
    each pair counts as an independent trial.
    """
    code = [landing for landing in landed if landing.code]
    chosen, used = [], set()
    for a, b in zip(code, code[1:]):
        if b.opened < a.merged and a.number not in used and b.number not in used:
            chosen.append((a, b))
            used |= {a.number, b.number}
    return chosen


def revert_messages(repo: Path, branch: str = "HEAD") -> list[str]:
    log = gitops.git(repo, "log", "--format=%B%x1e", branch)
    return [message for message in log.split("\x1e") if "revert" in message.lower()]


def is_reverted(landing: Landing, messages: list[str]) -> bool:
    """True if any commit reverts the landing, by SHA or by the subject a revert gives it."""
    subjects = (f'Revert "{landing.title}', f'Revert "Merge pull request #{landing.number} ')
    return any(
        f"This reverts commit {landing.commit}" in message or message.strip().startswith(subjects)
        for message in messages
    )


def _semantics(source: str) -> str | None:
    """Dump the module's AST without docstrings or annotations; None if it doesn't parse."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and body:
            first = body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                node.body = body[1:] or [ast.Pass()]
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            node.returns = None
        elif isinstance(node, ast.arg):
            node.annotation = None
        elif isinstance(node, ast.AnnAssign):
            node.annotation = ast.Constant(None)
    return ast.dump(tree)


def changes_runtime(repo: Path, landing: Landing) -> bool:
    """True if the landing changes package code beyond docstrings, annotations, comments, and layout.

    Such a side can hardly conflict with anything, so a pair with one is easy to
    call clean, and reports break it out.
    """
    for path in landing.code:
        before, after = (
            gitops.git(repo, "show", f"{sha}:{path}") if gitops.has_path(repo, sha, path) else None
            for sha in (landing.parent, landing.commit)
        )
        if before is None or after is None or _semantics(before) is None or _semantics(before) != _semantics(after):
            return True
    return False


_ASSISTED = re.compile(
    r"co-authored-by:[^\n]*\b(claude|copilot|codex|gpt|gemini|cursor|devin|anthropic|openai)\b"
    r"|generated with \[?(claude|copilot|codex|cursor)",
    re.IGNORECASE,
)


def is_assisted(repo: Path, landing: Landing) -> bool:
    """True if the pull request or its landing commit credits an AI assistant. Uncredited help goes uncounted."""
    message = gitops.git(repo, "log", "-1", "--format=%B", landing.commit)
    return bool(_ASSISTED.search(landing.body) or _ASSISTED.search(message))


def _line(text: str) -> str:
    # A JSON string is a valid TOML basic string.
    return json.dumps(text, ensure_ascii=False)


def _block(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\\", "\\\\").replace('"', '\\"')
    text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", lambda m: f"\\u{ord(m.group()):04x}", text)
    return f'"""\n{text}\n"""'


def case_toml(
    repo_name: str, a: Landing, b: Landing, tests: str | None = None,
    runtime: tuple[str, ...] = ("a", "b"), assisted: tuple[str, ...] = (),
) -> str:
    """Write a mined case. The text round-trips through tomllib, or this raises.

    ``runtime`` names the sides that change runtime code, and ``assisted`` the
    sides that credit an AI assistant. Reports break false positives out by both.
    """
    base = f'{{ repo = "{repo_name}", commit = "{a.parent}"' + (f", tests = {_line(tests)}" if tests else "") + " }"
    same = "same file" if set(a.code) & set(b.code) else "other files"
    text = (
        f'base = {base}\nlabel = "clean"\nclass = "mined, {same}"\n'
        f"runtime = {json.dumps(list(runtime))}\nassisted = {json.dumps(list(assisted))}\n"
    )
    for name, landing in (("a", a), ("b", b)):
        text += (
            f"\n[{name}]\ntitle = {_line(landing.title)}\npr = {_line(landing.url)}\n"
            f'from = "{landing.parent}"\nto = "{landing.commit}"\nbody = {_block(landing.body)}\n'
        )
    parsed = tomllib.loads(text)
    for name, landing in (("a", a), ("b", b)):
        if parsed[name]["title"] != landing.title or parsed[name]["body"].strip() != landing.body.replace("\r\n", "\n").strip():
            raise ValueError(f"case text for PR {landing.number} does not round-trip")
    return text


def suite_tests(repo: Path, commit: str, meta: dict) -> str | None:
    """Return where the suite lives at ``commit`` if it moved from the repository default, else None.

    ``former_tests`` in repos/<name>.toml lists where the suite lived before,
    a directory or a single file, tried after the default.
    """
    default = meta.get("tests", "tests")
    for candidate in (default, *meta.get("former_tests", ()), *(f"{p.rstrip('/')}/tests" for p in meta["packages"])):
        if gitops.has_path(repo, commit, candidate):
            return None if candidate == default else candidate
    return None


def mine(corpus: Path, name: str, clone: Path, prs: list[dict], cutoff: str) -> list[tuple[str, list[str]]]:
    """Write a candidate case for every mined pair; return each pair and why it was left out, if it was.

    ``clone`` holds the repository's full history; a blobless clone is enough.
    """
    repo_toml = corpus / "repos" / f"{name}.toml"
    meta = tomllib.loads(repo_toml.read_text())
    messages = revert_messages(clone)
    report = []
    for a, b in pairs(landings(clone, prs, tuple(meta["packages"]), cutoff)):
        case_id = f"{name}-{a.number}-x-{b.number}"
        if is_reverted(a, messages) or is_reverted(b, messages):
            report.append((case_id, ["a later commit reverts one side"]))
            continue
        dest = corpus / "cases" / case_id
        dest.mkdir(parents=True, exist_ok=True)  # the rule is deterministic, so a rerun rewrites the same case
        sides = (("a", a), ("b", b))
        (dest / "case.toml").write_text(case_toml(
            name, a, b, suite_tests(clone, a.parent, meta),
            runtime=tuple(n for n, x in sides if changes_runtime(clone, x)),
            assisted=tuple(n for n, x in sides if is_assisted(clone, x)),
        ))
        problems = _tree_fits(load_case(dest))
        if problems:
            shutil.rmtree(dest)
        report.append((case_id, problems))
    return report


def _tree_fits(case) -> list[str]:
    """A generator that can't see the base tree can only leave the pair unverified."""
    with tempfile.TemporaryDirectory(prefix="fourway-mine-") as tmp:
        try:
            render_tree(checkout_upstream(case.base, Path(tmp) / "tree"))
        except (TreeTooLarge, ValueError) as e:  # ValueError: export attributes would change the trees
            return [str(e)]
        except gitops.GitError as e:
            return [f"the case does not build: {e}"]
    return []

