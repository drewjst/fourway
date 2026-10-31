import sys
import doctest
import itertools
import toolz
import toolz.functoolz
import toolz.itertoolz
from toolz.itertoolz import interpose, take


def test_interpose_nonempty_unchanged():
    assert list(interpose('a', [1, 2, 3])) == [1, 'a', 2, 'a', 3]
    assert list(interpose('a', [1])) == [1]
    assert list(take(3, interpose(0, itertools.count(1)))) == [1, 0, 2]
    assert ''.join(interpose('X', 'tarzan')) == 'tXaXrXzXaXn'


def test_functoolz_pypy_flag_still_correct():
    assert hasattr(toolz.functoolz, 'PYPY')
    assert toolz.functoolz.PYPY == hasattr(sys, 'pypy_version_info')


def test_module_doctests_pass():
    assert doctest.testmod(toolz.itertoolz).failed == 0
    assert doctest.testmod(toolz.functoolz).failed == 0
