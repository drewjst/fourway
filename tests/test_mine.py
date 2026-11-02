"""The mining rule decides which real pairs count as clean, so each clause must hold exactly."""

import tomllib
from dataclasses import replace

import pytest

from fourway import gitops
from fourway.case import load_case
from fourway.mine import (
    Landing, case_toml, changes_runtime, is_assisted, is_code, is_reverted, landings, mine, pairs, suite_tests,
)

T = "2026-01-0{}T00:00:00Z"


def landing(number: int, opened: int, merged: int, code: tuple[str, ...] = ("pkg/core.py",)) -> Landing:
    return Landing(
        number=number, url=f"https://example.com/pull/{number}", title=f"Change {number}", body="",
        opened=T.format(opened), merged=T.format(merged), parent=f"{number:040x}",
        commit=f"{number + 100:040x}", code=code,
    )


def numbers(chosen):
    return [(a.number, b.number) for a, b in chosen]


def test_a_pair_needs_the_second_pull_request_open_when_the_first_landed():
    """A pull request opened after the first landed was written against it, so it isn't concurrent."""
    assert numbers(pairs([landing(1, 1, 3), landing(2, 2, 4)])) == [(1, 2)]
    assert numbers(pairs([landing(1, 1, 3), landing(2, 3, 4)])) == []


def test_no_pull_request_joins_two_pairs():
    """Pairs that share a change aren't independent trials, and the interval assumes they are."""
    chosen = pairs([landing(1, 1, 3), landing(2, 2, 5), landing(3, 4, 6), landing(4, 5, 7)])
    assert numbers(chosen) == [(1, 2), (3, 4)]


def test_a_landing_without_package_code_neither_pairs_nor_separates_a_pair():
    """A docs-only landing can't conflict semantically; pairing it would pad the clean count."""
    docs = landing(2, 2, 3, code=())
    assert numbers(pairs([landing(1, 1, 3), docs, landing(3, 2, 4)])) == [(1, 3)]


def test_only_package_python_outside_tests_is_code():
    packages = ("pkg/", "src/pkg/")
    assert is_code("pkg/core.py", packages) and is_code("src/pkg/sub/x.py", packages)
    assert not is_code("pkg/tests/test_core.py", packages)
    assert not is_code("pkg/test/harness.py", packages)  # pyflakes keeps its suite in pyflakes/test/
    assert not is_code("pkg/test_core.py", packages)
    assert not is_code("docs/conf.py", packages)
    assert not is_code("pkg/data.json", packages)


@pytest.fixture
def history(tmp_path):
    """A default branch with every kind of landing the rule must tell apart."""
    repo = gitops.init(tmp_path / "repo")

    def land(path, subject, text="x = 1\n"):
        (repo / path).parent.mkdir(parents=True, exist_ok=True)
        (repo / path).write_text(text)
        return gitops.commit_all(repo, subject)

    land("README.md", "start")
    squash = land("pkg/a.py", "Add a (#1)")
    rebased = land("pkg/b.py", "Add b, rebased")
    bot = land("pkg/c.py", "Bump c (#3)")
    late = land("pkg/d.py", "Add d (#4)")
    gitops.git(repo, "checkout", "--quiet", "-b", "topic")
    land("pkg/e.py", "Add e")
    gitops.git(repo, "checkout", "--quiet", "main")
    gitops.git(repo, "merge", "--quiet", "--no-ff", "-m", "Merge pull request #5 from someone/topic", "topic")
    merged = gitops.git(repo, "rev-parse", "HEAD")
    land("tests/test_x.py", "Test x (#6)")
    tests_only = gitops.git(repo, "rev-parse", "HEAD")

    def pr(number, sha, merged_at=2, user="someone", user_type="User"):
        return {
            "number": number, "html_url": f"https://example.com/pull/{number}", "title": f"PR {number}",
            "body": None, "user": user, "user_type": user_type, "created_at": T.format(1),
            "merged_at": T.format(merged_at), "merge_commit_sha": sha,
        }

    prs = [
        pr(1, squash), pr(2, rebased), pr(3, bot, user="dependabot[bot]", user_type="Bot"),
        pr(4, late, merged_at=9), pr(5, merged), pr(6, tests_only),
    ]
    return repo, prs


def test_landings_keep_squash_and_merge_commits_from_people_before_the_cutoff(history):
    """A rebase merge spans commits the history can't delimit; a bot's change isn't a person's."""
    repo, prs = history
    found = landings(repo, prs, ("pkg/",), cutoff=T.format(5))
    assert [landing.number for landing in found] == [1, 5, 6]
    assert [landing.code for landing in found] == [("pkg/a.py",), ("pkg/e.py",), ()]
    assert all(gitops.git(repo, "rev-parse", f"{x.commit}^") == x.parent for x in found)


def test_a_revert_by_sha_or_by_subject_drops_the_landing():
    """A reverted change shipped broken or was withdrawn, so the history doesn't vouch for the merge."""
    one = landing(1, 1, 2)
    assert is_reverted(one, [f"Revert stuff\n\nThis reverts commit {one.commit}.\n"])
    assert is_reverted(one, ['Revert "Change 1 (#1)" (#9)\n'])
    assert is_reverted(replace(one, title="x"), ['Revert "Merge pull request #1 from a/b"\n'])
    assert not is_reverted(one, ['Revert "Other change (#10)"\n', "Mention revert without reverting\n"])


def test_case_text_round_trips_any_pull_request_text(tmp_path):
    """Upstream titles and bodies carry quotes, backslashes, and CRLF; a mangled description is a different change."""
    nasty = 'Fix "quotes", \\back\\slashes, """triples""", tabs\there,\r\nCRLF lines, and a bell \x07 and ünïcode'
    a = replace(landing(1, 1, 3), title='Say "hi" \\o/', body=nasty)
    b = replace(landing(2, 2, 4), body="")
    (tmp_path / "repos").mkdir()
    (tmp_path / "repos" / "pkg.toml").write_text('url = "file:///nowhere"\nlicense = "MIT"\npackages = ["pkg/"]\n')
    case_dir = tmp_path / "cases" / "pkg-1-x-2"
    case_dir.mkdir(parents=True)
    (case_dir / "case.toml").write_text(case_toml("pkg", a, b, tests="pkg/tests"))

    case = load_case(case_dir)
    assert case.mined and case.label == "clean" and case.expect is None
    assert case.a.intent.title == a.title and case.a.intent.body == nasty.replace("\r\n", "\n").strip()
    assert case.a.commits == (a.parent, a.commit) and case.b.commits == (b.parent, b.commit)
    assert case.base.commit == a.parent and case.suite.tests == "pkg/tests"
    assert tomllib.loads((case_dir / "case.toml").read_text())["class"] == "mined, same file"


CODE = '''"""Module doc."""


def wait(attempt: int) -> float:
    """Return the wait."""
    limit: float = 2.0
    return min(attempt * 1.5, limit)
'''


@pytest.mark.parametrize("after, runtime", [
    (CODE.replace("Return the wait.", "Return the wait, in seconds."), False),
    (CODE.replace("attempt: int", "attempt: float").replace(") -> float", ") -> int"), False),
    (CODE.replace("limit: float = 2.0", "limit: int = 2.0  # cap"), False),
    (CODE.replace("min(attempt * 1.5, limit)", "min(\n        attempt * 1.5,\n        limit,\n    )"), False),
    (CODE.replace("1.5", "2.5"), True),
    (CODE.replace("min(", "max("), True),
])
def test_a_side_changes_runtime_only_if_the_code_beyond_docs_and_annotations_changes(tmp_path, after, runtime):
    """A side that only edits docs, types, or layout can hardly conflict; reports must not count it as hard."""
    repo = gitops.init(tmp_path / "repo")
    (repo / "pkg").mkdir()
    (repo / "pkg" / "wait.py").write_text(CODE)
    parent = gitops.commit_all(repo, "base")
    (repo / "pkg" / "wait.py").write_text(after)
    commit = gitops.commit_all(repo, "change (#1)")
    side = replace(landing(1, 1, 2, code=("pkg/wait.py",)), parent=parent, commit=commit)
    assert changes_runtime(repo, side) is runtime


def test_a_new_package_file_changes_runtime(tmp_path):
    repo = gitops.init(tmp_path / "repo")
    (repo / "README.md").write_text("x\n")
    parent = gitops.commit_all(repo, "base")
    (repo / "pkg").mkdir()
    (repo / "pkg" / "new.py").write_text('"""Only a docstring."""\n')
    commit = gitops.commit_all(repo, "add (#1)")
    assert changes_runtime(repo, replace(landing(1, 1, 2, code=("pkg/new.py",)), parent=parent, commit=commit))


def test_an_ai_credit_in_the_description_or_the_commit_marks_a_side_assisted(tmp_path):
    """Pairs a model helped write share the generator's blind spots, so reports break them out."""
    repo = gitops.init(tmp_path / "repo")
    (repo / "x.py").write_text("x = 1\n")
    plain = gitops.commit_all(repo, "Change (#1)")
    (repo / "x.py").write_text("x = 2\n")
    trailer = gitops.commit_all(repo, "Change (#2)\n\nCo-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>")
    base = landing(1, 1, 2)
    assert not is_assisted(repo, replace(base, commit=plain, body="Fixes #3. Co-authored with my colleague."))
    assert is_assisted(repo, replace(base, commit=plain, body="Done.\n\n🤖 Generated with [Claude Code](https://claude.com)"))
    assert is_assisted(repo, replace(base, commit=trailer))


def test_a_pair_whose_trees_git_archive_would_rewrite_is_reported_not_written(tmp_path, monkeypatch):
    """versioneer's export-subst gives each exported tree different bytes; such a pair drops with its reason."""
    monkeypatch.setenv("FOURWAY_CACHE", str(tmp_path / "cache"))
    repo = gitops.init(tmp_path / "upstream")
    (repo / ".gitattributes").write_text("pkg/_version.py export-subst\n")
    (repo / "pkg").mkdir()
    (repo / "pkg" / "_version.py").write_text('refs = "$Format:%d$"\n')
    gitops.commit_all(repo, "start")
    prs = []
    for n in (1, 2):
        (repo / "pkg" / f"m{n}.py").write_text("x = 1\n")
        prs.append({
            "number": n, "html_url": f"https://example.com/pull/{n}", "title": f"Add m{n}", "body": "",
            "user": "someone", "user_type": "User", "created_at": T.format(1), "merged_at": T.format(1 + n),
            "merge_commit_sha": gitops.commit_all(repo, f"Add m{n} (#{n})"),
        })
    corpus = tmp_path / "corpus"
    (corpus / "repos").mkdir(parents=True)
    (corpus / "repos" / "pkg.toml").write_text(f'url = "file://{repo}"\nlicense = "MIT"\npackages = ["pkg/"]\n')

    [(case_id, problems)] = mine(corpus, "pkg", repo, prs, cutoff=T.format(9))
    assert case_id == "pkg-1-x-2" and "export attributes" in problems[0]
    assert not (corpus / "cases" / case_id).exists()


def test_a_case_names_where_the_suite_lived_at_its_base(tmp_path):
    """pycodestyle's suite was testsuite/ before it was tests/; the default path would run no tests at all."""
    repo = gitops.init(tmp_path / "repo")
    (repo / "testsuite").mkdir()
    (repo / "testsuite" / "test_all.py").write_text("")
    (repo / "test_mod.py").write_text("")
    old = gitops.commit_all(repo, "old layout")
    meta = {"packages": ["mod.py"], "former_tests": ["testsuite", "test_mod.py"]}
    assert suite_tests(repo, old, meta) == "testsuite"
    (repo / "testsuite" / "test_all.py").unlink()
    assert suite_tests(repo, gitops.commit_all(repo, "single file"), meta) == "test_mod.py"
    (repo / "tests").mkdir()
    (repo / "tests" / "test_all.py").write_text("")
    assert suite_tests(repo, gitops.commit_all(repo, "new layout"), meta) is None
