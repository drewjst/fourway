import tenacity
from tenacity import retry


def test_not_exception_message_and_unless_type_semantics() -> None:
    calls = {"n": 0}

    @retry(
        stop=tenacity.stop_after_attempt(6),
        retry=tenacity.retry_if_not_exception_message(match="^stop.*"),
    )
    def fn() -> None:
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("keep going")
        raise RuntimeError("stop now")

    try:
        fn()
    except RuntimeError as exc:
        assert str(exc) == "stop now"
    else:
        raise AssertionError("expected RuntimeError")
    assert calls["n"] == 3
    assert fn.statistics["attempt_number"] == 3

    ucalls = {"n": 0}

    @retry(
        stop=tenacity.stop_after_attempt(10),
        retry=tenacity.retry_unless_exception_type(KeyError),
    )
    def ufn() -> int:
        ucalls["n"] += 1
        if ucalls["n"] < 4:
            return ucalls["n"]
        raise KeyError("done")

    try:
        ufn()
    except KeyError:
        pass
    else:
        raise AssertionError("expected KeyError")
    assert ucalls["n"] == 4
    assert ufn.statistics["attempt_number"] == 4


def test_exception_message_and_type_semantics() -> None:
    calls = {"n": 0}

    @retry(
        stop=tenacity.stop_after_attempt(5),
        retry=tenacity.retry_if_exception_message(message="retry me"),
    )
    def fn() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise ValueError("retry me")
        return "ok"

    assert fn() == "ok"
    assert calls["n"] == 3
    assert fn.statistics["attempt_number"] == 3

    ncalls = {"n": 0}

    @retry(
        stop=tenacity.stop_after_attempt(5),
        retry=tenacity.retry_if_not_exception_type(TypeError),
    )
    def nfn() -> None:
        ncalls["n"] += 1
        if ncalls["n"] < 2:
            raise ValueError("retry")
        raise TypeError("no retry")

    try:
        nfn()
    except TypeError:
        pass
    else:
        raise AssertionError("expected TypeError")
    assert ncalls["n"] == 2
    assert nfn.statistics["attempt_number"] == 2
