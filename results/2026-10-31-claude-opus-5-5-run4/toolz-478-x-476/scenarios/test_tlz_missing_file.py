import types

import toolz
from tlz._build_tlz import TlzLoader


def _make_fake():
    fake = types.ModuleType('fake_toolz_like')
    assert not hasattr(fake, '__file__')

    def helper(x):
        return x * 2

    fake.helper = helper
    fake.pipe = toolz.pipe
    return fake


def test_exec_module_tolerates_missing_file():
    fake = _make_fake()
    loader = TlzLoader()
    loader._load_toolz = lambda fullname: {'toolz': fake}
    target = types.ModuleType('tlz_fake_target_mod')
    loader.exec_module(target)
    assert target.helper(3) == 6
    assert target.pipe is toolz.pipe
    assert not hasattr(target, '__file__')


def test_exec_module_missing_file_with_both_backends():
    fast = _make_fake()
    slow = _make_fake()
    loader = TlzLoader()
    loader._load_toolz = lambda fullname: {'cytoolz': fast, 'toolz': slow}
    target = types.ModuleType('tlz_fake_target_mod2')
    loader.exec_module(target)
    assert target.helper is fast.helper
    assert target.pipe is toolz.pipe
