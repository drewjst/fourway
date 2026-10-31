import asyncio

import tenacity
from tenacity import AsyncRetrying, Retrying, retry, retry_if_result, stop_after_attempt, wait_fixed


def test_sync_retrying_callstate_repr_in_before_sleep():
    reprs = []
    sleeps = []
    calls = {'n': 0}

    def fn():
        calls['n'] += 1
        if calls['n'] == 1:
            raise ValueError('boom')
        if calls['n'] == 2:
            return None
        return 'ok'

    r = Retrying(
        sleep=sleeps.append,
        wait=wait_fixed(0.5),
        stop=stop_after_attempt(5),
        retry=tenacity.retry_if_exception_type() | retry_if_result(lambda x: x is None),
        before_sleep=lambda rs: reprs.append(repr(rs)),
    )
    assert r(fn) == 'ok'
    assert sleeps == [0.5, 0.5]
    assert len(reprs) == 2
    assert reprs[0].startswith('<RetryCallState ')
    assert reprs[0].endswith('attempt #1; slept for 0.5; last result: failed (ValueError boom)>')
    assert reprs[1].endswith('attempt #2; slept for 1.0; last result: returned None>')


def test_async_retrying_callstate_repr_via_decorator_and_call():
    reprs = []
    slept = []

    async def fake_sleep(s):
        slept.append(s)

    state = {'n': 0}

    @retry(sleep=fake_sleep, wait=wait_fixed(0.25), stop=stop_after_attempt(4),
           before_sleep=lambda rs: reprs.append(repr(rs)))
    async def flaky():
        state['n'] += 1
        if state['n'] < 3:
            raise KeyError('k')
        return 7

    assert isinstance(flaky.retry, AsyncRetrying)
    assert asyncio.run(flaky()) == 7
    assert slept == [0.25, 0.25]
    assert reprs[0].endswith("attempt #1; slept for 0.25; last result: failed (KeyError 'k')>")
    assert reprs[1].endswith("attempt #2; slept for 0.5; last result: failed (KeyError 'k')>")

    captured = []

    async def returns_none():
        return None

    ar = AsyncRetrying(sleep=fake_sleep, stop=stop_after_attempt(2),
                       retry=retry_if_result(lambda x: x is None),
                       retry_error_callback=lambda rs: captured.append(repr(rs)) or 'gave up')
    assert asyncio.run(ar(returns_none)) == 'gave up'
    assert captured[0].endswith('attempt #2; slept for 0.0; last result: returned None>')
