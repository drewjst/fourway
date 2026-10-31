import pickle
from operator import add
from itertools import starmap
from toolz import join, first, second, identity

no_default2 = pickle.loads(pickle.dumps('__no__default__'))


def test_inner_join_many_to_many_and_sentinel_copy():
    names = [(1, 'one'), (2, 'two'), (3, 'three'), (1, 'uno')]
    fruit = [('apple', 1), ('orange', 1), ('banana', 2), ('kiwi', 9)]
    expected = [((1, 'one'), ('apple', 1)), ((1, 'uno'), ('apple', 1)),
                ((1, 'one'), ('orange', 1)), ((1, 'uno'), ('orange', 1)),
                ((2, 'two'), ('banana', 2))]
    assert list(join(first, names, second, fruit)) == expected
    assert list(join(first, names, second, fruit,
                     left_default=no_default2,
                     right_default=no_default2)) == expected
    # non-callable keys behave as getters
    assert list(join(0, names, 1, fruit)) == expected


def test_right_and_left_outer_joins_order_and_duplicates():
    assert list(join(identity, [1, 2], identity, [2, 3, 3],
                     left_default=None)) == [(2, 2), (None, 3), (None, 3)]
    assert list(join(identity, [1, 1, 2], identity, [2],
                     right_default=None)) == [(2, 2), (1, None), (1, None)]
    assert list(join(identity, [1, 2], identity, [2, 3],
                     left_default='L', right_default=no_default2)) == [(2, 2), ('L', 3)]


def test_full_outer_join():
    assert list(join(identity, [1, 2, 3], identity, [2, 3, 4],
                     left_default=None, right_default=None)) == \
        [(2, 2), (3, 3), (None, 4), (1, None)]
    assert list(join(identity, [], identity, [5],
                     left_default=0, right_default=0)) == [(0, 5)]
    assert list(join(identity, [5], identity, [],
                     left_default=0, right_default=0)) == [(5, 0)]


def test_right_sequence_consumed_lazily():
    pulled = []

    def right():
        for i in [1, 2, 3, 4]:
            pulled.append(i)
            yield i

    it = join(identity, [1, 2, 3, 4], identity, right())
    assert next(it) == (1, 1)
    assert pulled == [1]
    it = join(identity, [1, 2], identity, right(), left_default=None)
    pulled[:] = []
    assert next(it) == (1, 1)
    assert pulled == [1]
    rest = list(it)
    assert rest == [(2, 2), (None, 3), (None, 4)]
