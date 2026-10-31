import doctest
import warnings

import semver
from semver import Version

METHODS = [
    Version.bump_major,
    Version.bump_minor,
    Version.bump_patch,
    Version.bump_prerelease,
    Version.bump_build,
    Version.next_version,
]


def _run_doctests(func):
    finder = doctest.DocTestFinder(recurse=False)
    tests = finder.find(func, func.__name__, globs={"semver": semver, "Version": Version})
    runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
    total_fail = 0
    total_tried = 0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for t in tests:
            res = runner.run(t, out=lambda s: None)
            total_fail += res.failed
            total_tried += res.attempted
    return total_fail, total_tried


def test_docstring_examples_execute_cleanly():
    for func in METHODS:
        failed, tried = _run_doctests(func)
        assert tried > 0, func.__name__
        assert failed == 0, "doctest failed for %s" % func.__name__


def test_docstrings_do_not_use_deprecated_parse():
    for func in METHODS:
        doc = func.__doc__ or ""
        assert "semver.Version.parse(" in doc, func.__name__
        assert "semver.parse(" not in doc, func.__name__
