import pytest
import toolz
import toolz.curried
from toolz import join, identity, first, second


def test_apply_exposed_and_uncurried():
    from toolz.functoolz import apply
    assert toolz.apply is apply
    assert toolz.curried.apply is apply
    assert not isinstance(toolz.curried.apply, toolz.curry)
    assert isinstance(toolz.curried.join, toolz.curry)
    assert apply(lambda x: 2 * x, 5) == 10
    with pytest.raises(TypeError):
        apply()


def test_apply_forwards_kwargs_to_join_modes():
    apply = toolz.apply
    L, R = [1, 2, 3], [2, 3, 4]
    assert list(apply(join, identity, L, identity, R)) == [(2, 2), (3, 3)]
    assert list(apply(join, identity, L, identity, R, left_default=None)) == \
        [(2, 2), (3, 3), (None, 4)]
    assert list(apply(join, identity, L, identity, R, right_default=None)) == \
        [(2, 2), (3, 3), (1, None)]
    assert list(apply(join, identity, L, identity, R,
                      left_default=None, right_default=None)) == \
        [(2, 2), (3, 3), (None, 4), (1, None)]


def test_map_apply_over_join_results():
    apply = toolz.apply
    names = [(1, 'one'), (2, 'two')]
    fruit = [('apple', 1), ('banana', 2), ('cherry', 7)]
    pairs = list(join(first, names, second, fruit, left_default=(0, '?')))
    funcs = [lambda p: p[0][1] + ':' + p[1][0]] * len(pairs)
    assert list(map(apply, funcs, pairs)) == ['one:apple', 'two:banana', '?:cherry']
    cjoin = toolz.curried.join(identity, [1, 2], identity)
    assert list(toolz.curried.apply(cjoin, [2, 5])) == [(2, 2)]
