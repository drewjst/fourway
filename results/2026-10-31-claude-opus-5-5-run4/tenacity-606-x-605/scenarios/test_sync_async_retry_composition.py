import asyncio

from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt
from tenacity import asyncio as tasyncio
from tenacity.asyncio import retry as aretry


def test_sync_or_async_yields_async_retry_any_and_behaves():
    async def lt_3(x):
        return x < 3

    strategy = retry_if_exception_type(KeyError) | tasyncio.retry_if_result(lt_3)
    assert isinstance(strategy, aretry.retry_any)

    async def run():
        attempts = 0
        async for attempt in AsyncRetrying(retry=strategy, stop=stop_after_attempt(10)):
            with attempt:
                attempts += 1
            if not attempt.retry_state.outcome.failed:
                attempt.retry_state.set_result(attempts)
        return attempts

    assert asyncio.run(run()) == 3


def test_sync_and_async_yields_async_retry_all():
    async def lt_3(x):
        return x < 3

    def gt_0(x):
        return x > 0

    from tenacity import retry_if_result

    strategy = retry_if_result(gt_0) & tasyncio.retry_if_result(lt_3)
    assert isinstance(strategy, aretry.retry_all)

    async def run():
        attempts = 0
        async for attempt in AsyncRetrying(retry=strategy, stop=stop_after_attempt(10)):
            with attempt:
                attempts += 1
            attempt.retry_state.set_result(attempts)
        return attempts

    assert asyncio.run(run()) == 3
