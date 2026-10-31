import asyncio

import tenacity
from tenacity import retry


def test_retry_object_statistics_track_attempts_with_message_strategy() -> None:
    seen: list[int] = []

    @retry(
        stop=tenacity.stop_after_attempt(5),
        retry=tenacity.retry_if_not_exception_message(message="final"),
        reraise=True,
    )
    def fn() -> None:
        seen.append(fn.retry.statistics["attempt_number"])
        if len(seen) < 3:
            raise ValueError("transient")
        raise ValueError("final")

    try:
        fn()
    except ValueError as exc:
        assert str(exc) == "final"
    else:
        raise AssertionError("expected ValueError")

    assert seen == [1, 2, 3]
    assert fn.retry.statistics["attempt_number"] == 3
    assert fn.retry.statistics == fn.statistics


def test_async_retry_object_statistics_track_attempts_with_type_strategy() -> None:
    seen: list[int] = []

    @retry(
        stop=tenacity.stop_after_attempt(4),
        retry=tenacity.retry_if_exception_type(ValueError),
        reraise=True,
    )
    async def afn() -> str:
        seen.append(afn.retry.statistics["attempt_number"])
        if len(seen) < 3:
            raise ValueError("again")
        return "ok"

    result = asyncio.run(afn())
    assert result == "ok"
    assert seen == [1, 2, 3]
    assert afn.retry.statistics["attempt_number"] == 3
    assert afn.retry.statistics == afn.statistics
