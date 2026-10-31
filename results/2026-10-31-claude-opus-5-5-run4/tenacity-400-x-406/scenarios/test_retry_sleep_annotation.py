import sys
import typing as t

import pytest

import tenacity


@pytest.mark.skipif(not hasattr(t, "get_overloads"), reason="typing.get_overloads requires Python 3.11+")
def test_retry_overload_sleep_accepts_awaitable_return():
    overloads = t.get_overloads(tenacity.retry)
    target = None
    for ov in overloads:
        if "sleep" in getattr(ov, "__annotations__", {}):
            target = ov
            break
    assert target is not None, "no retry overload with a sleep parameter"
    ann = target.__annotations__["sleep"]
    args = t.get_args(ann)
    assert len(args) == 2
    ret = args[1]
    assert ret == t.Optional[t.Awaitable[None]]
