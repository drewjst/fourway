import itertools
from operator import add

import pytest

from toolz import accumulate, second


def test_second_of_accumulate_values():
    assert second(accumulate(add, [1, 2, 3])) == 3
    assert second(accumulate(add, [1, 2], 10)) == 11
    assert second(accumulate(add, iter([4, 5, 6]))) == 9


def test_second_consumes_exactly_two_items():
    it = accumulate(add, [1, 2, 3, 4])
    assert second(it) == 3
    assert next(it) == 6
    assert list(it) == [10]


def test_second_on_infinite_accumulate():
    assert second(accumulate(add, itertools.count(1))) == 3


def test_second_of_single_item_accumulate_raises_stopiteration():
    with pytest.raises(StopIteration):
        second(accumulate(add, [5]))
    with pytest.raises(StopIteration):
        second(accumulate(add, [], 7))
