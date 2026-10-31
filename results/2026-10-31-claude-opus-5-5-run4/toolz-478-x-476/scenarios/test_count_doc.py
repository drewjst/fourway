import toolz
from toolz.itertoolz import count


def test_count_docstring_fixed():
    assert 'lazy sequences' in count.__doc__
    assert 'sequencies' not in count.__doc__
    assert toolz.count is count


def test_tlz_count_docstring_when_pure_python():
    import tlz
    if tlz.count is toolz.count:
        assert 'lazy sequences' in tlz.count.__doc__
    assert count(iter(range(4))) == 4
