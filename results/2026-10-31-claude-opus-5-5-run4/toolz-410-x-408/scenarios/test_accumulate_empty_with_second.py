import itertools
from operator import add

import pytest

from toolz import accumulate, second, first, pipe
from toolz import curried


def test_accumulate_empty_without_initial_yields_nothing():
    assert list(accumulate(add, [])) == []
    assert list(accumulate(add, iter([]))) == []
    assert list(pipe([], curried.accumulate(add))) == []


def test_second_and_first_of_empty_accumulate_raise_stopiteration():
    with pytest.raises(StopIteration):
        second(accumulate(add, []))
    with pytest.raises(StopIteration):
        second(accumulate(add, iter([])))
    with pytest.raises(StopIteration):
        first(accumulate(add, []))
    # wrapping in chain must not surface RuntimeError either
    assert list(itertools.chain(accumulate(add, []), [1])) == [1]
