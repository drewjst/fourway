import toolz
from toolz import curry
from toolz.curried import get, map as cmap
from toolz.curried import operator as cop
from toolz.functoolz import is_partial_args, has_varargs, num_required_args


def test_curry_partial_application_repeated():
    @curry
    def add3(x, y, z=0):
        return x + y + z

    inc = add3(1)
    assert inc(2) == 3
    assert inc(2) == 3
    assert add3(1)(2, z=4) == 7
    assert add3(z=1)(1)(1) == 3


def test_curry_builtins_and_curried_namespace():
    assert list(curry(map)(lambda v: v + 1)([1, 2])) == [2, 3]
    assert list(cmap(str)([1, 2])) == ['1', '2']
    assert get(0)((5, 6)) == 5
    assert cop.add(1)(2) == 3
    assert num_required_args(map) == 2
    assert has_varargs(map)
    assert is_partial_args(map, (), {}) is True
    assert has_varargs(1) is False
