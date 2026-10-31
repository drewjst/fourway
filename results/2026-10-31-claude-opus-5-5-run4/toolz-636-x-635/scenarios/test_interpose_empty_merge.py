import toolz
import toolz.curried
from toolz.itertoolz import interpose


def test_interpose_empty_list_and_generator():
    assert list(interpose('a', [])) == []
    assert list(interpose('a', (x for x in []))) == []
    assert list(interpose(0, iter(()))) == []


def test_interpose_empty_via_curried_and_compose():
    f = toolz.curried.interpose('-')
    assert list(f([])) == []
    g = toolz.compose(list, toolz.curried.interpose('-'))
    assert g([]) == []
    assert g('ab') == ['a', '-', 'b']


def test_interpose_empty_via_tlz():
    import tlz
    assert list(tlz.interpose('x', [])) == []
    assert list(tlz.interpose('x', [1, 2])) == [1, 'x', 2]
