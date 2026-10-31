import toolz
import toolz.compatibility as compat
from toolz.dicttoolz import assoc


def test_py26_py33_compat_shims_removed():
    assert not hasattr(compat, 'PY33')
    assert 'import_module' not in compat.__all__
    assert not hasattr(compat, 'import_module')
    # the rest of the package still works without the shim
    assert assoc({'a': 1}, 'b', 2) == {'a': 1, 'b': 2}
    assert toolz.merge({1: 1}, {2: 2}) == {1: 1, 2: 2}
