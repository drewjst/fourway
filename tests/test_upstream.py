"""Cases whose base is a pinned commit of another repository, built from a local stand-in for it."""

from pathlib import Path

import pytest

from fourway import bench, gitops
from fourway.case import load_corpus, materialize

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
