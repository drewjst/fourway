import asyncio

import pytest

from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt


def test_async_with_retries_on_composed_strategy():
    strategy = retry_if_exception_type(KeyError) | retry_if_exception_type(ValueError)

    async def run():
        attempts = 0
        async for attempt in AsyncRetrying(retry=strategy, stop=stop_after_attempt(5)):
            async with attempt:
                attempts += 1
                if attempts < 3:
                    raise ValueError("again")
        return attempts

    assert asyncio.run(run()) == 3


def test_async_with_non_retryable_propagates_after_one_attempt():
    strategy = retry_if_exception_type(KeyError) | retry_if_exception_type(ValueError)
    calls = []

    async def run():
        async for attempt in AsyncRetrying(retry=strategy, stop=stop_after_attempt(5)):
            async with attempt:
                calls.append(1)
                raise TypeError("nope")

    with pytest.raises(TypeError):
        asyncio.run(run())
    assert calls == [1]
