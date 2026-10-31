import toolz
import toolz.functoolz


def test_real_tlz_mirrors_toolz():
    import tlz
    import tlz.functoolz
    assert tlz.__file__ == toolz.__file__
    assert tlz.functoolz.__file__ == toolz.functoolz.__file__
    assert tlz.pipe is toolz.pipe
    assert tlz.count([1, 2, 3]) == 3
    assert tlz.count(iter([1, 2])) == 2
