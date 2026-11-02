"""Cases whose base is a pinned commit of another repository, built from a local stand-in for it."""

import shutil
from pathlib import Path

import pytest

from fourway import bench, gitops
from fourway.case import load_case, load_corpus, materialize

FLAG_A_ON = """\
diff --git a/src/pkg/fa.py b/src/pkg/fa.py
--- a/src/pkg/fa.py
+++ b/src/pkg/fa.py
@@ -1 +1 @@
-ON = False
+ON = True
"""
FLAG_B_ON = FLAG_A_ON.replace("fa.py", "fb.py")
ORACLE = "from pkg import fa, fb\n\n\ndef test_flags_are_not_both_on():\n    assert not (fa.ON and fb.ON)\n"


def make_upstream(root: Path, extra: dict | None = None) -> tuple[Path, str]:
    """A src-layout package whose pytest.ini breaks unless fourway overrides addopts."""
    files = {
        "src/pkg/__init__.py": "",
        "src/pkg/fa.py": "ON = False\n",
        "src/pkg/fb.py": "ON = False\n",
        "pytest.ini": "[pytest]\naddopts = --flag-only-a-plugin-knows\n",
        "tests/test_pkg.py": (
            "import pytest\n\nfrom pkg import fa\n\n\n"
            "def test_flag_a_is_a_bool():\n    assert fa.ON in (True, False)\n\n\n"
            "def test_needs_an_optional_dependency():\n    pytest.importorskip('fourway_absent_module')\n"
        ),
        **(extra or {}),
    }
    repo = gitops.init(root)
    for name, text in files.items():
        (repo / name).parent.mkdir(parents=True, exist_ok=True)
        (repo / name).write_text(text)
    return repo, gitops.commit_all(repo, "upstream")


def make_corpus(root: Path, upstream: Path, commit: str) -> Path:
    (root / "repos").mkdir(parents=True)
    (root / "repos" / "pkg.toml").write_text(
        f'url = "file://{upstream}"\ncommit = "{commit}"\nlicense = "MIT"\n'
        'tests = "tests"\npythonpath = ["src"]\npytest_args = ["-o", "addopts="]\n'
    )
    case = root / "cases" / "flags"
    (case / "oracle").mkdir(parents=True)
    (case / "case.toml").write_text(
        'base = { repo = "pkg" }\nlabel = "conflict"\nexpect = "emergent"\nclass = "flags"\n\n'
        '[a]\ntitle = "Turn on flag A"\nbody = "A."\n\n[b]\ntitle = "Turn on flag B"\nbody = "B."\n'
    )
    (case / "a.patch").write_text(FLAG_A_ON)
    (case / "b.patch").write_text(FLAG_B_ON)
    (case / "oracle" / "test_flags.py").write_text(ORACLE)
    return root


@pytest.fixture(autouse=True)
def cache(tmp_path, monkeypatch):
    monkeypatch.setenv("FOURWAY_CACHE", str(tmp_path / "cache"))


def test_a_case_on_a_pinned_commit_checks_like_a_corpus_case(tmp_path):
    """Patches apply, src/ is importable, addopts is overridden, and a skipped upstream test is not red."""
    upstream, commit = make_upstream(tmp_path / "upstream")
    [case] = load_corpus(make_corpus(tmp_path / "corpus", upstream, commit))
    assert bench.check_case(case) == []


def test_the_pinned_commit_is_fetched_once(tmp_path):
    """After the first fetch, cases build from the cache, so a moved or deleted upstream cannot change them."""
    upstream, commit = make_upstream(tmp_path / "upstream")
    [case] = load_corpus(make_corpus(tmp_path / "corpus", upstream, commit))
    first = materialize(case, tmp_path / "one")
    gitops.git(upstream, "commit", "--quiet", "--allow-empty", "-m", "later")
    (upstream / ".git").rename(upstream / "moved.git")
    second = materialize(case, tmp_path / "two")
    assert (first.base, first.a, first.b) == (second.base, second.a, second.b)


def test_a_commit_the_upstream_does_not_have_is_refused(tmp_path):
    upstream, _ = make_upstream(tmp_path / "upstream")
    [case] = load_corpus(make_corpus(tmp_path / "corpus", upstream, "0" * 40))
    with pytest.raises(gitops.GitError):
        materialize(case, tmp_path / "work")


def test_a_short_sha_is_refused(tmp_path):
    """A branch name or short SHA can move or become ambiguous; the base must not."""
    upstream, commit = make_upstream(tmp_path / "upstream")
    with pytest.raises(ValueError, match="full 40-character SHA"):
        load_corpus(make_corpus(tmp_path / "corpus", upstream, commit[:12]))


def test_export_attributes_are_refused(tmp_path):
    """git archive would silently drop an export-ignore path from every tree the scenarios run on."""
    upstream, commit = make_upstream(tmp_path / "upstream", {".gitattributes": "tests/ export-ignore\n"})
    [case] = load_corpus(make_corpus(tmp_path / "corpus", upstream, commit))
    with pytest.raises(ValueError, match="export attributes"):
        materialize(case, tmp_path / "work")


def mined_case(root: Path, upstream: Path, base: str, a: tuple[str, str], b: tuple[str, str], extra: str = "") -> Path:
    (root / "repos").mkdir(parents=True)
    (root / "repos" / "pkg.toml").write_text(
        f'url = "file://{upstream}"\nlicense = "MIT"\npackages = ["src/pkg/"]\n'
        'tests = "tests"\npythonpath = ["src"]\npytest_args = ["-o", "addopts="]\n'
    )
    case = root / "cases" / "pkg-1-x-2"
    case.mkdir(parents=True)
    (case / "case.toml").write_text(
        f'base = {{ repo = "pkg", commit = "{base}" }}\nlabel = "clean"\nclass = "mined, other files"\n{extra}\n'
        f'[a]\ntitle = "A"\nbody = ""\nfrom = "{a[0]}"\nto = "{a[1]}"\n\n'
        f'[b]\ntitle = "B"\nbody = ""\nfrom = "{b[0]}"\nto = "{b[1]}"\n'
    )
    return case


def land(upstream: Path, path: str, text: str) -> str:
    (upstream / path).write_text(text)
    return gitops.commit_all(upstream, f"change {path}")


def tree(repo: Path, sha: str) -> str:
    return gitops.git(repo, "rev-parse", f"{sha}^{{tree}}")


def test_sides_named_by_commits_rebuild_the_upstream_history(tmp_path):
    """A is the first landing as shipped, and the merge is the second landing as shipped; only B alone is new."""
    upstream, base = make_upstream(tmp_path / "upstream")
    first = land(upstream, "src/pkg/fa.py", "ON = True\n")
    second = land(upstream, "src/pkg/fb.py", "ON = True\n")
    case = load_case(mined_case(tmp_path / "corpus", upstream, base, (base, first), (first, second)))

    pair = materialize(case, tmp_path / "work")
    assert tree(pair.repo, pair.base) == tree(upstream, base)
    assert tree(pair.repo, pair.a) == tree(upstream, first)
    assert tree(pair.repo, gitops.merge(pair.repo, pair.a, pair.b)) == tree(upstream, second)
    assert gitops.git(pair.repo, "show", f"{pair.b}:src/pkg/fa.py") == "ON = False"
    assert bench.check_case(case) == []


def test_a_change_written_on_top_of_the_other_does_not_build(tmp_path):
    """B edits a line only A added, so B alone isn't a change anyone could have proposed against the base."""
    upstream, base = make_upstream(tmp_path / "upstream")
    first = land(upstream, "src/pkg/fa.py", "ON = False\nLIMIT = 1\n")
    second = land(upstream, "src/pkg/fa.py", "ON = False\nLIMIT = 2\n")
    case = load_case(mined_case(tmp_path / "corpus", upstream, base, (base, first), (first, second)))
    [problem] = bench.check_case(case)
    assert "does not build" in problem


def test_only_a_clean_pair_from_history_goes_without_an_oracle(tmp_path):
    """Without an oracle, nothing but the history backs the label, and history can only say a merge shipped."""
    upstream, base = make_upstream(tmp_path / "upstream")
    first = land(upstream, "src/pkg/fa.py", "ON = True\n")
    path = mined_case(tmp_path / "corpus", upstream, base, (base, first), (base, first))
    text = (path / "case.toml").read_text()
    (path / "case.toml").write_text(text.replace('label = "clean"', 'label = "conflict"'))
    with pytest.raises(ValueError, match="only a clean pair mined from history"):
        load_case(path)
    (path / "case.toml").write_text(text.replace('commit = "', 'comit = "'))
    with pytest.raises(ValueError, match="unknown keys in base"):
        load_case(path)


def test_pruning_deletes_only_failing_mined_pairs(tmp_path, capsys):
    """A seeded case or a mined conflict encodes an answer someone wrote by hand; pruning may never delete one."""
    from fourway.cli import main

    upstream, base = make_upstream(tmp_path / "upstream")
    first = land(upstream, "src/pkg/fa.py", "ON = False\nLIMIT = 1\n")
    second = land(upstream, "src/pkg/fa.py", "ON = False\nLIMIT = 2\n")
    corpus = tmp_path / "corpus"
    broken_mined = mined_case(corpus, upstream, base, (base, first), (first, second))
    seeded = corpus / "cases" / "seeded"
    (seeded / "oracle").mkdir(parents=True)
    (seeded / "case.toml").write_text(
        f'base = {{ repo = "pkg", commit = "{base}" }}\nlabel = "clean"\nexpect = "ok"\nclass = "s"\n\n'
        '[a]\ntitle = "A"\nbody = ""\n\n[b]\ntitle = "B"\nbody = ""\n'
    )  # no oracle files, so the check fails
    relabeled = corpus / "cases" / "pkg-3-x-4"
    shutil.copytree(broken_mined, relabeled)
    text = (relabeled / "case.toml").read_text()
    (relabeled / "case.toml").write_text(text.replace('label = "clean"', 'label = "conflict"\nexpect = "differential_b"'))
    (relabeled / "oracle").mkdir()  # likewise empty

    assert main(["check-corpus", "--corpus", str(corpus), "--prune-mined"]) == 1
    assert not broken_mined.exists() and seeded.exists() and relabeled.exists()
    out = capsys.readouterr().out
    assert f"drop  {broken_mined.name}" in out and "FAIL  seeded" in out and f"FAIL  {relabeled.name}" in out


def test_only_a_test_that_fails_alike_on_all_four_trees_is_ignored(tmp_path):
    """Such a test fails in this environment, not because of A or B; a file that can't import hides its tests."""
    always_red = "def test_needs_another_python():\n    assert False\n"
    upstream, commit = make_upstream(tmp_path / "up1", {"tests/test_env.py": always_red})
    [case] = load_corpus(make_corpus(tmp_path / "c1", upstream, commit))
    assert bench.check_case(case) == []

    upstream, commit = make_upstream(tmp_path / "up2", {"tests/test_env.py": "import fourway_absent_module\n"})
    [case] = load_corpus(make_corpus(tmp_path / "c2", upstream, commit))
    assert any("test_env.py is error" in p for p in bench.check_case(case))

    upstream, commit = make_upstream(tmp_path / "up3", {"tests/test_pkg.py": always_red})
    [case] = load_corpus(make_corpus(tmp_path / "c3", upstream, commit))
    assert "existing suite: no test passes on all four trees" in bench.check_case(case)
