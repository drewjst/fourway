import re

import pytest

import tenacity
from tenacity import Future, RetryCallState, Retrying


def _state(exc):
    rs = RetryCallState(None, None, (), {})
    rs.outcome = Future.construct(1, exc, True)
    return rs


def test_copy_preserves_and_overrides_with_none():
    def cb(rs):
        return "cb"

    def bs(rs):
        return None

    r = Retrying(name="orig", before_sleep=bs, retry_error_callback=cb)
    c = r.copy()
    assert str(c) == "orig"
    assert c.before_sleep is bs
    assert c.retry_error_callback is cb
    c2 = r.copy(name=None, before_sleep=None, retry_error_callback=None)
    assert str(c2) == "<unknown>"
    assert c2.before_sleep is None
    assert c2.retry_error_callback is None


def test_retry_if_exception_message_match_behaviour():
    r = tenacity.retry_if_exception_message(match="boo.*")
    assert isinstance(r.match, re.Pattern)
    assert r.message is None
    assert r(_state(RuntimeError("boom")))
    assert not r(_state(RuntimeError("nope")))
    p = tenacity.retry_if_exception_message(match=re.compile("x+"))
    assert p(_state(ValueError("xxx")))
    m = tenacity.retry_if_exception_message(message="hi")
    assert m.match is None
    assert m(_state(ValueError("hi")))
    with pytest.raises(TypeError):
        tenacity.retry_if_exception_message()


def test_retry_with_message_match_end_to_end():
    calls = []
    sleeps = []

    @tenacity.retry(
        sleep=sleeps.append,
        stop=tenacity.stop_after_attempt(5),
        retry=tenacity.retry_if_exception_message(match="again"),
    )
    def f():
        calls.append(1)
        if len(calls) < 3:
            raise ValueError("again")
        return "done"

    assert f() == "done"
    assert len(calls) == 3
    assert f.statistics["attempt_number"] == 3
    calls.clear()
    assert f.retry_with(before_sleep=None, name=None)() == "done"
    assert len(calls) == 3
