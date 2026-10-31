import asyncio
import re

import pytest

import tenacity
from tenacity import (
    AsyncRetrying,
    RetryError,
    Retrying,
    retry_if_exception_message,
    retry_if_not_exception_message,
    stop_after_attempt,
)


def _noop_sleep(seconds):
    return None


def test_reraise_last_exception_with_compiled_match_pattern():
    raised = []

    def fn():
        exc = ValueError(f"boom {len(raised) + 1}")
        raised.append(exc)
        raise exc

    r = Retrying(
        sleep=_noop_sleep,
        stop=stop_after_attempt(3),
        retry=retry_if_exception_message(match=re.compile(r"boom")),
        reraise=True,
    )
    with pytest.raises(ValueError) as ei:
        r(fn)
    assert len(raised) == 3
    assert ei.value is raised[-1]
    assert str(ei.value) == "boom 3"
    assert not isinstance(ei.value, RetryError)
    assert r.statistics["attempt_number"] == 3


def test_reraise_non_matching_message_not_retried_with_compiled_pattern():
    calls = []

    def fn():
        calls.append(1)
        raise KeyError("other")

    r = Retrying(
        sleep=_noop_sleep,
        stop=stop_after_attempt(5),
        retry=retry_if_exception_message(match=re.compile(r"boom")),
        reraise=True,
    )
    with pytest.raises(KeyError):
        r(fn)
    assert len(calls) == 1


def test_reraise_with_successful_last_attempt_raises_retry_error():
    calls = []

    def fn():
        calls.append(1)
        return None

    # retry_if_not_exception_message always retries when there is no exception
    r = Retrying(
        sleep=_noop_sleep,
        stop=stop_after_attempt(2),
        retry=retry_if_not_exception_message(match=re.compile(r"never")),
        reraise=True,
    )
    with pytest.raises(RetryError) as ei:
        r(fn)
    assert len(calls) == 2
    assert ei.value.last_attempt.attempt_number == 2
    assert not ei.value.last_attempt.failed


def test_reraise_context_manager_with_compiled_pattern():
    raised = []

    class MyErr(Exception):
        pass

    def run():
        for attempt in Retrying(
            sleep=_noop_sleep,
            stop=stop_after_attempt(2),
            retry=retry_if_exception_message(match=re.compile(r"fail")),
            reraise=True,
        ):
            with attempt:
                exc = MyErr("fail now")
                raised.append(exc)
                raise exc

    with pytest.raises(MyErr) as ei:
        run()
    assert len(raised) == 2
    assert ei.value is raised[-1]


def test_async_reraise_with_compiled_pattern():
    raised = []

    async def fake_sleep(seconds):
        return None

    async def fn():
        exc = RuntimeError(f"boom {len(raised) + 1}")
        raised.append(exc)
        raise exc

    async def main():
        r = AsyncRetrying(
            sleep=fake_sleep,
            stop=stop_after_attempt(3),
            retry=retry_if_exception_message(match=re.compile(r"boom")),
            reraise=True,
        )
        return await r(fn)

    with pytest.raises(RuntimeError) as ei:
        asyncio.run(main())
    assert len(raised) == 3
    assert ei.value is raised[-1]


def test_no_reraise_wraps_in_retry_error_with_cause():
    def fn():
        raise ValueError("boom")

    r = Retrying(
        sleep=_noop_sleep,
        stop=stop_after_attempt(2),
        retry=retry_if_exception_message(match=re.compile(r"boom")),
    )
    with pytest.raises(RetryError) as ei:
        r(fn)
    assert isinstance(ei.value.__cause__, ValueError)
    assert ei.value.last_attempt.attempt_number == 2
    assert tenacity.RetryError is RetryError
