import toolz
import toolz.curried


def test_compose_left_exported_uncurried_from_curried():
    from toolz.curried import compose_left
    assert compose_left is toolz.compose_left
    assert compose_left is toolz.functoolz.compose_left
    assert not isinstance(compose_left, toolz.curry)
    assert 'compose_left' in toolz.functoolz.__all__


def test_compose_left_with_curried_functions():
    from toolz.curried import compose_left, map, get, filter
    f = compose_left(map(get(0)), filter(lambda x: x > 1), list)
    assert f([(1, 'a'), (3, 'b'), (5, 'c')]) == [3, 5]
    assert compose_left()(7) == 7

    def add_then_multiply(a, b, c=10):
        return (a + b) * c

    inc = lambda x: x + 1
    assert compose_left(add_then_multiply, inc, str)(1, 2, c=3) == '10'
