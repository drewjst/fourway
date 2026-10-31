import inspect
import re
import types
import typing

import tenacity
from tenacity import BaseRetrying
from tenacity.asyncio import AsyncRetrying
from tenacity.retry import retry_if_exception_message

NoneType = type(None)


def _args(fn, name):
    ann = inspect.signature(fn).parameters[name].annotation
    args = typing.get_args(ann)
    assert args, f"{name} annotation is not a union: {ann!r}"
    return args


def test_copy_unions_end_with_none():
    for name in ("before_sleep", "retry_error_callback", "name"):
        args = _args(BaseRetrying.copy, name)
        assert args[-1] is NoneType, (name, args)
        assert object in args, (name, args)


def test_match_and_async_unions_end_with_none():
    args = _args(retry_if_exception_message.__init__, "match")
    assert args[-1] is NoneType, args
    assert args[0] is str, args
    for name in ("before", "after"):
        ann = inspect.signature(AsyncRetrying.__init__).parameters[name].annotation
        cargs = typing.get_args(ann)
        ret = cargs[-1]
        inner = typing.get_args(ret)
        assert inner[-1] is NoneType, (name, inner)
