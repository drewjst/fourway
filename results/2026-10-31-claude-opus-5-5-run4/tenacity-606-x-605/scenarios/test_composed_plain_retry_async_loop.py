import asyncio

import pytest

from tenacity import AsyncRetrying, Retrying, retry_if_exception_type, stop_after_attempt


def _is_value_error(retry_state):
    return retry_state.outcome is not None and isinstance(retry_state.outcome.exception(), ValueError)


def test_or_with_plain_function_in_async_for():
    strategy = retry_if_exception_type(KeyError) | _is_value_error

    async def run():
        attempts = 0
        async for attempt in AsyncRetrying(retry=strategy, stop=stop_after_attempt(5)):
            with attempt:
                attempts += 1
                if attempts < 3:
                    raise ValueError("again")
        return attempts

    assert asyncio.run(run()) == 3


def test_and_with_plain_function_stops_when_plain_says_no():
    def under_three(retry_state):
        return retry_state.attempt_number < 3

    strategy = retry_if_exception_type(ValueError) & under_three
    calls = []

    async def run():
        async for attempt in AsyncRetrying(retry=strategy, stop=stop_after_attempt(10), reraise=True):
            with attempt:
                calls.append(1)
                raise ValueError("boom")

    with pytest.raises(ValueError):
        asyncio.run(run())
    assert len(calls) == 3

    sync_calls = []

    def fn():
        sync_calls.append(1)
        raise ValueError("boom")

    with pytest.raises(ValueError):
        Retrying(retry=strategy, stop=stop_after_attempt(10))(fn)
    assert len(sync_calls) == 3
