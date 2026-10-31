import asyncio
import random
from unittest import mock

import pytest

import tenacity
from tenacity import RetryError, retry, stop_after_attempt, wait_fixed, wait_random_exponential


def test_patch_sync_retry_wait_with_random_exponential(monkeypatch):
    sleeps = []

    @retry(sleep=lambda s: sleeps.append(float(s)), stop=stop_after_attempt(3), wait=wait_fixed(100))
    def f():
        raise ValueError("boom")

    monkeypatch.setattr(random, "uniform", lambda a, b: b)

    with mock.patch.object(f.retry, "wait", wait_random_exponential(multiplier=1, min=3, max=10)):
        with pytest.raises(RetryError):
            f()

    assert sleeps == [3.0, 3.0]
    assert f.statistics["attempt_number"] == 3
    assert f.statistics["idle_for"] == pytest.approx(6.0)

    # after the patch is removed, original wait is used again
    sleeps.clear()
    with pytest.raises(RetryError):
        f()
    assert sleeps == [100.0, 100.0]


def test_patch_async_retry_wait_with_random_exponential(monkeypatch):
    sleeps = []

    async def fake_sleep(s):
        sleeps.append(float(s))

    @retry(sleep=fake_sleep, stop=stop_after_attempt(3), wait=wait_fixed(100))
    async def f():
        raise ValueError("boom")

    monkeypatch.setattr(random, "uniform", lambda a, b: b)

    with mock.patch.object(f.retry, "wait", wait_random_exponential(multiplier=1, min=4, max=10)):
        with pytest.raises(RetryError):
            asyncio.run(f())

    assert sleeps == [4.0, 4.0]
    assert f.statistics["attempt_number"] == 3
