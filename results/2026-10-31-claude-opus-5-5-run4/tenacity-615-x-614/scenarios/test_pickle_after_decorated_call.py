import pickle

import tenacity
from tenacity import Retrying, retry


def test_retry_object_picklable_after_decorated_call() -> None:
    calls = {"n": 0}

    @retry(
        stop=tenacity.stop_after_attempt(3),
        retry=tenacity.retry_if_exception_type(ValueError),
        reraise=True,
    )
    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise ValueError("not yet")
        return "ok"

    assert flaky() == "ok"
    assert flaky.statistics["attempt_number"] == 3

    # After the call the original retry object may hold live statistics in
    # its thread-local storage; pickling must still work.
    restored = pickle.loads(pickle.dumps(flaky.retry))
    assert isinstance(restored, Retrying)
    assert restored.statistics == {}

    counter = {"n": 0}

    def other() -> str:
        counter["n"] += 1
        if counter["n"] < 2:
            raise ValueError("again")
        return "done"

    assert restored(other) == "done"
    assert counter["n"] == 2
    assert restored.statistics["attempt_number"] == 2


def test_restored_retrying_wraps_and_populates_statistics() -> None:
    original = Retrying(
        stop=tenacity.stop_after_attempt(3),
        retry=tenacity.retry_if_exception_message(message="boom"),
        reraise=True,
    )
    restored = pickle.loads(pickle.dumps(original))

    state = {"n": 0}

    def fn() -> str:
        state["n"] += 1
        if state["n"] % 3 != 0:
            raise ValueError("boom")
        return "ok"

    wrapped = restored.wraps(fn)
    assert wrapped() == "ok"
    assert wrapped.statistics["attempt_number"] == 3
    # Calling again works and refreshes statistics.
    assert wrapped() == "ok"
    assert wrapped.statistics["attempt_number"] == 3
    assert state["n"] == 6

    # Non-matching message must not be retried.
    def other() -> None:
        raise ValueError("different")

    other_wrapped = restored.wraps(other)
    try:
        other_wrapped()
    except ValueError as exc:
        assert str(exc) == "different"
    else:
        raise AssertionError("expected ValueError")
    assert other_wrapped.statistics["attempt_number"] == 1
