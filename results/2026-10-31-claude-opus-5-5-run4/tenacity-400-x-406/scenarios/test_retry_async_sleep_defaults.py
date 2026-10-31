import asyncio
import inspect

import tenacity
from tenacity import retry, stop_after_attempt, wait_fixed


async def _fake_async_sleep(seconds):
    _fake_async_sleep.calls.append(seconds)


_fake_async_sleep.calls = []


def test_async_retry_with_async_sleep_preserves_defaults_and_kwdefaults():
    @retry(sleep=_fake_async_sleep, stop=stop_after_attempt(3), wait=wait_fixed(0.5))
    async def fn(a, b=2, *, c=3):
        return (a, b, c)

    assert inspect.iscoroutinefunction(fn)
    assert fn.__defaults__ == (2,)
    assert fn.__kwdefaults__ == {"c": 3}
    assert asyncio.run(fn(1)) == (1, 2, 3)


def test_async_retry_with_copy_preserves_defaults():
    @retry(sleep=_fake_async_sleep, stop=stop_after_attempt(3))
    async def fn(x=10, *, y=20):
        return x + y

    copied = fn.retry_with(stop=stop_after_attempt(5), wait=wait_fixed(0.25))
    assert copied.__defaults__ == (10,)
    assert copied.__kwdefaults__ == {"y": 20}
    assert asyncio.run(copied()) == 30
