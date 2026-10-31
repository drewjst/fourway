import doctest

import toolz.itertoolz as itz
import toolz.dicttoolz as dtz
from toolz.itertoolz import groupby


def _run_doctests(obj, module):
    finder = doctest.DocTestFinder()
    runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS)
    failed = 0
    attempted = 0
    for test in finder.find(obj, globs=dict(vars(module))):
        res = runner.run(test, out=lambda s: None)
        failed += res.failed
        attempted += res.attempted
    return failed, attempted


def test_docstring_examples_still_pass():
    failed, _ = _run_doctests(itz.groupby, itz)
    assert failed == 0
    failed, attempted = _run_doctests(dtz.update_in, dtz)
    assert failed == 0
    assert attempted > 0


def test_groupby_behavior_unchanged():
    assert groupby(lambda x: x % 2 == 0, [1, 2, 3, 4]) == {True: [2, 4], False: [1, 3]}
    assert groupby(0, [(1, 2), (1, 3), (2, 2)]) == {1: [(1, 2), (1, 3)], 2: [(2, 2)]}
