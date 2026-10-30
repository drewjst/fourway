"""Evidence ledger: append-only, content-addressed records of what was verified.

A record answers "has this combination been verified?" only while its guards
hold: the four commit SHAs, the test environment, and the scenario set. When
any of them moves, lookups stop matching. Nothing expires on a clock.
"""

from __future__ import annotations

import hashlib
import json
import platform
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

import pytest

from . import __version__
from .pipeline import FourWay

SCHEMA = "fourway.evidence/v0"


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def env_digest() -> str:
    return _digest(_canonical({
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "pytest": pytest.__version__,
        "platform": f"{platform.system()}-{platform.machine()}",
        "fourway": __version__,
    }))


def scenarios_digest(scenarios: Mapping[str, str]) -> str:
    return _digest(_canonical({name: _digest(src.encode()) for name, src in scenarios.items()}))


def record(
    result: FourWay,
    scenarios: Mapping[str, str],
    *,
    generator: str,
    models: Sequence[str] = (),
    config: Mapping | None = None,
    repeat: int = 1,
) -> dict:
    body = {
        "schema": SCHEMA,
        "guards": {
            **result.shas,
            "env": env_digest(),
            "scenarios": scenarios_digest(scenarios),
        },
        "generator": {"name": generator, "models": sorted(models), "config": dict(config or {})},
        "repeat": repeat,
        "tests": {
            test: {**result.outcomes[test], "finding": result.findings[test]}
            for test in sorted(result.outcomes)
        },
        "verdict": result.verdict,
    }
    # recorded_at stays outside the hashed body, so re-running the same
    # verification yields the same id.
    return {"id": _digest(_canonical(body)), **body, "recorded_at": datetime.now(UTC).isoformat()}


def append(path: Path, rec: Mapping) -> bool:
    """Append ``rec`` unless a record with its id is already there. Return whether it was written."""
    if path.exists() and any(json.loads(line)["id"] == rec["id"] for line in path.read_text().splitlines()):
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
    return True


def lookup(path: Path, guards: Mapping[str, str]) -> dict | None:
    """Return the latest record whose guards include every given guard, or None."""
    if not path.exists():
        return None
    match = None
    for line in path.read_text().splitlines():
        rec = json.loads(line)
        if all(rec["guards"].get(key) == value for key, value in guards.items()):
            match = rec
    return match
