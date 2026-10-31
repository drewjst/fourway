import toolz
import toolz.curried


def test_curried_peekn_partial_application():
    from toolz.curried import peekn
    assert isinstance(peekn, toolz.curry)
    assert peekn.func is toolz.peekn
    peek_two = peekn(2)
    head, rest = peek_two(iter([10, 20, 30, 40]))
    assert head == (10, 20)
    assert list(rest) == [10, 20, 30, 40]


def test_peekn_toplevel_short_sequence_and_generator():
    from toolz import peekn
    gen = (i * i for i in range(3))
    head, rest = peekn(5, gen)
    assert head == (0, 1, 4)
    assert tuple(rest) == (0, 1, 4)
    head, rest = peekn(0, [1, 2])
    assert head == ()
    assert list(rest) == [1, 2]
    assert 'peekn' in toolz.itertoolz.__all__
