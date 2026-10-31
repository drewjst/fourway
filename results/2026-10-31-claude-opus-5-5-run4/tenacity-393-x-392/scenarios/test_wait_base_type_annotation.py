import typing

import tenacity
from tenacity import wait as tw


def test_wait_base_t_callable_returns_numeric():
    args = typing.get_args(tw.WaitBaseT)
    assert tw.wait_base in args
    callables = [a for a in args if typing.get_origin(a) is not None and a is not tw.wait_base]
    assert len(callables) == 1
    params, ret = typing.get_args(callables[0])
    assert ret is not bool
    assert ret == typing.Union[float, int]
    assert set(typing.get_args(ret)) == {float, int}


def test_wait_base_t_still_reachable_from_package():
    # the alias lives in tenacity.wait, which the package imports
    assert tenacity.wait.WaitBaseT is tw.WaitBaseT
