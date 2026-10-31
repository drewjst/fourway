import asyncio
from unittest import mock

import pytest

import tenacity
from tenacity import AsyncRetrying, Retrying, stop_after_attempt


def test_sync_direct_call_disabled_raises_original_once():
    calls = []

    def fails():
        calls.append(1)
        raise ValueError("fail")

    with mock.patch.object(tenacity, "tornado", None):
        r = Retrying(enabled=False, stop=stop_after_attempt(5), sleep=lambda s: None)
        with pytest.raises(ValueError, match="fail"):
            r(fails)
    assert len(calls) == 1


def test_async_direct_call_disabled_raises_original_once():
    calls = []

    async def fails():
        calls.append(1)
        raise ValueError("fail")

    async def no_sleep(s):
        return None

    r = AsyncRetrying(enabled=False, stop=stop_after_attempt(5), sleep=no_sleep)

    async def main():
        await r(fails)

    with pytest.raises(ValueError, match="fail"):
        asyncio.run(main())
    assert len(calls) == 1


def test_async_direct_call_disabled_sync_fn_raises_original_once():
    calls = []

    def fails():
        calls.append(1)
        raise KeyError("boom")

    async def no_sleep(s):
        return None

    r = AsyncRetrying(enabled=False, stop=stop_after_attempt(4), sleep=no_sleep)

    async def main():
        await r(fails)

    with pytest.raises(KeyError):
        asyncio.run(main())
    assert len(calls) == 1
