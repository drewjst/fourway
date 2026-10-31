import re
import typing

import pytest

import tenacity
from tenacity import Retrying, stop_after_attempt


def _has_pattern(ann):
    return any(typing.get_origin(a) is re.Pattern for a in typing.get_args(ann))


def test_match_annotation_accepts_pattern():
    for cls in (
        tenacity.retry_if_exception_message,
        tenacity.retry_if_not_exception_message,
    ):
        ann = cls.__init__.__annotations__["match"]
        assert _has_pattern(ann), (cls, ann)


def test_retry_with_keeps_compiled_pattern_strategy():
    calls = []

    @tenacity.retry(
        sleep=lambda s: None,
        stop=stop_after_attempt(2),
        retry=tenacity.retry_if_exception_message(match=re.compile(r"^busy", re.IGNORECASE)),
        reraise=True,
    )
    def f():
        calls.append(1)
        if len(calls) < 4:
            raise RuntimeError("BUSY now")
        raise KeyError("fatal")

    g = f.retry_with(stop=stop_after_attempt(10))
    with pytest.raises(KeyError):
        g()
    assert len(calls) == 4


def test_copy_with_not_exception_message_compiled_pattern():
    template = Retrying(
        sleep=lambda s: None,
        stop=stop_after_attempt(1),
        retry=tenacity.retry_if_not_exception_message(match=re.compile(r"fatal")),
        reraise=True,
    )
    r = template.copy(stop=stop_after_attempt(10))
    assert isinstance(r, Retrying)

    calls = []

    def f():
        calls.append(1)
        if len(calls) < 3:
            raise RuntimeError("busy")
        raise RuntimeError("fatal error")

    with pytest.raises(RuntimeError, match="fatal error"):
        r(f)
    assert len(calls) == 3
