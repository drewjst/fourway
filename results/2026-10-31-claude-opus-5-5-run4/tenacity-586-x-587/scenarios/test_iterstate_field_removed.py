import dataclasses

import pytest

import tenacity
from tenacity import IterState, Retrying


def test_iterstate_has_no_delay_field():
    names = {f.name for f in dataclasses.fields(IterState)}
    assert "delay_since_first_attempt" not in names
    state = IterState()
    with pytest.raises(AttributeError):
        state.delay_since_first_attempt  # noqa: B018
    with pytest.raises(TypeError):
        IterState(delay_since_first_attempt=0)  # type: ignore[call-arg]


def test_iter_state_after_run_lacks_field_but_stats_have_delay():
    calls = []

    def f():
        calls.append(1)
        if len(calls) < 3:
            raise ValueError("boom")
        return "ok"

    r = Retrying(sleep=lambda s: None, stop=tenacity.stop_after_attempt(5))
    assert r(f) == "ok"
    assert not hasattr(r.iter_state, "delay_since_first_attempt")
    assert r.iter_state.retry_run_result is False
    assert r.statistics["attempt_number"] == 3
    assert isinstance(r.statistics["delay_since_first_attempt"], float)
    assert r.statistics["delay_since_first_attempt"] >= 0
