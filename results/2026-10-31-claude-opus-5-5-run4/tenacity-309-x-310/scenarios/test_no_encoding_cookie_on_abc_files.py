import re
import tokenize
from pathlib import Path

import pytest

COOKIE = re.compile(r"^[ \t\f]*#.*?coding[:=]")

FILES = [
    "tenacity/__init__.py",
    "tenacity/retry.py",
    "tenacity/stop.py",
    "tenacity/wait.py",
]


@pytest.mark.parametrize("rel", FILES)
def test_shared_files_have_no_encoding_cookie(rel):
    lines = Path(rel).read_text(encoding="utf-8").splitlines()[:2]
    for line in lines:
        assert not COOKIE.match(line), "%s still declares encoding: %r" % (rel, line)


@pytest.mark.parametrize("rel", FILES)
def test_shared_files_compile_as_utf8_without_cookie(rel):
    data = Path(rel).read_bytes()
    with open(rel, "rb") as fh:
        enc, _ = tokenize.detect_encoding(fh.readline)
    assert enc == "utf-8"
    compile(data, rel, "exec")
