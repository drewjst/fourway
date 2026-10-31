import doctest
from itertools import count, islice

import toolz.sandbox.core as core
from toolz.sandbox.core import unzip


def test_unzip_infinite_outer_sequence_is_lazy():
    a, b = unzip(zip(count(0), count(10)))
    assert list(islice(a, 3)) == [0, 1, 2]
    assert list(islice(b, 3)) == [10, 11, 12]
    assert list(unzip(iter([]))) == []


def test_sandbox_core_doctests_pass():
    result = doctest.testmod(core)
    assert result.failed == 0
