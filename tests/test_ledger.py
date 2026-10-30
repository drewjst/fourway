from fourway import ledger
from fourway.pipeline import FourWay

SHAS = {"base": "b0", "a": "a1", "b": "b1", "ab": "m1"}
RESULT = FourWay(
    shas=SHAS,
    outcomes={"t::x": {"base": "passed", "a": "passed", "b": "passed", "ab": "failed"}},
    findings={"t::x": "emergent"},
    verdict="conflict",
)
SCENARIOS = {"test_x.py": "def test_x(): assert False\n"}


def test_the_same_verification_gets_the_same_id():
    """Re-running a verification must deduplicate, not grow the ledger with look-alike records."""
    first = ledger.record(RESULT, SCENARIOS, generator="oracle")
    second = ledger.record(RESULT, SCENARIOS, generator="oracle")
    assert first["id"] == second["id"]


def test_a_different_scenario_set_is_different_evidence():
    first = ledger.record(RESULT, SCENARIOS, generator="oracle")
    second = ledger.record(RESULT, {"test_x.py": "def test_x(): pass\n"}, generator="oracle")
    assert first["guards"]["scenarios"] != second["guards"]["scenarios"]
    assert first["id"] != second["id"]


def test_evidence_stops_matching_when_any_commit_moves(tmp_path):
    """Stale evidence must not answer "has this combination been verified?" with yes."""
    path = tmp_path / "ledger.jsonl"
    rec = ledger.record(RESULT, SCENARIOS, generator="oracle")
    ledger.append(path, rec)
    assert ledger.lookup(path, {"base": "b0", "a": "a1", "b": "b1"})["id"] == rec["id"]
    assert ledger.lookup(path, {"base": "b0", "a": "a2", "b": "b1"}) is None
    assert ledger.lookup(path, {"base": "b0", "a": "a1", "b": "b1", "env": "sha256:other"}) is None


def test_lookup_returns_the_latest_matching_record(tmp_path):
    path = tmp_path / "ledger.jsonl"
    old = ledger.record(RESULT, SCENARIOS, generator="oracle")
    new = ledger.record(RESULT, SCENARIOS, generator="null")
    ledger.append(path, old)
    ledger.append(path, new)
    assert ledger.lookup(path, SHAS)["generator"]["name"] == "null"
