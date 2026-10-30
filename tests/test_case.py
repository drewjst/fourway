import os
from pathlib import Path

from fourway import gitops
from fourway.case import Case, Intent, Side, materialize


def test_an_overlay_file_that_looks_unchanged_to_git_is_still_committed(tmp_path):
    """Found on CI: same size and same mtime as the base file made git skip B's change.

    The pair then merged to the base behavior, and a seeded conflict read as
    clean. Every file here has the same length and the same old mtime, which is
    what a fresh checkout of the corpus produces.
    """
    old = 946684800
    files = {
        tmp_path / "base" / "events.py": 'NAME = "charge.succeeded"\n',
        tmp_path / "a" / "other.py": "X = 1\n",
        tmp_path / "b" / "events.py": 'NAME = "payment.captured"\n',
    }
    for path, text in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        os.utime(path, (old, old))
    case = Case(
        id="same-size",
        path=tmp_path,
        base=tmp_path / "base",
        label="conflict",
        expect="emergent",
        conflict_class="test",
        a=Side(Intent("a", ""), tmp_path / "a", ()),
        b=Side(Intent("b", ""), tmp_path / "b", ()),
    )
    pair = materialize(case, tmp_path / "work")
    assert "payment.captured" in gitops.diff(pair.repo, pair.base, pair.b)
    assert "payment.captured" in gitops.git(pair.repo, "show", f"{pair.b}:events.py")
