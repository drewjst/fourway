import asyncio
import re

import pytest

import tenacity
from tenacity import AsyncRetrying, BaseRetrying, Retrying, stop_after_attempt


def test_copy_return_annotation_is_self():
    ann = BaseRetrying.copy.__annotations__.get("return")
    assert "Self" in str(ann), ann


def test_async_template_copy_is_async_iterable_with_compiled_match():
    async def nosleep(seconds):
        return None

    template = AsyncRetrying(
        sleep=nosleep,
        stop=stop_after_attempt(5),
        retry=tenacity.retry_if_exception_message(match=re.compile(r"transient.*")),
        reraise=True,
    )

    async def run():
        attempts = 0
        r = template.copy()
        assert type(r) is AsyncRetrying
        async for attempt in r:
            with attempt:
                attempts += 1
                if attempts < 3:
                    raise ValueError("transient failure")
        return attempts

    assert asyncio.run(run()) == 3

    async def run_fatal():
        attempts = 0
        async for attempt in template.copy():
            with attempt:
                attempts += 1
                raise ValueError("fatal problem")
        return attempts

    with pytest.raises(ValueError, match="fatal problem"):
        asyncio.run(run_fatal())


def test_subclass_copy_preserves_class_and_pattern_strategy():
    class MyRetrying(Retrying):
        pass

    pat = re.compile(r"^busy")
    template = MyRetrying(
        sleep=lambda s: None,
        stop=stop_after_attempt(3),
        retry=tenacity.retry_if_exception_message(match=pat),
    )
    c = template.copy(stop=stop_after_attempt(10))
    assert type(c) is MyRetrying
    assert c.retry is template.retry

    calls = []

    def f():
        calls.append(1)
        if len(calls) < 5:
            raise RuntimeError("busy now")
        return "ok"

    assert c(f) == "ok"
    assert len(calls) == 5
