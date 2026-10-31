"""The sandboxed runner must give the local runner's outcomes, and must fail loud when it can't run.

Tests that need Docker skip when the sandbox isn't built. CI sets
FOURWAY_REQUIRE_SANDBOX, so there they fail instead of skipping.
"""

import dataclasses
import os
import re
import sys
import tomllib
from pathlib import Path

import pytest

from fourway import bench, cli, generators, ledger, pipeline, runner
from fourway.case import load_corpus
from test_bench import CORPUS
from test_pipeline import A_ON, B_ON, FLAGS, make_pair

ROOT = Path(__file__).parents[1]


@pytest.fixture(scope="module")
def sandbox():
    try:
        return runner.Sandbox.resolve()
    except runner.SandboxError as e:
        if os.environ.get("FOURWAY_REQUIRE_SANDBOX"):
            pytest.fail(f"FOURWAY_REQUIRE_SANDBOX is set, but the sandbox can't run: {e}")
        pytest.skip(str(e))


def test_the_image_tests_with_the_locked_versions():
    """A sandboxed run and a local run must differ only in where they run. If the image's pytest or a
    corpus suite's dependency drifted from uv.lock, a mined pair that check-corpus passed could fail
    inside the sandbox, and its scenarios would score as broken."""
    lock = {p["name"]: p["version"] for p in tomllib.loads((ROOT / "uv.lock").read_text())["package"]}
    pins = re.findall(r"^([a-z0-9-]+)==([^ ;\\]+)", (ROOT / "sandbox" / "requirements.txt").read_text(), re.M)
    assert {"pytest", "pluggy", "typeguard", "click"} <= {name for name, _ in pins}
    for name, version in pins:
        assert lock[name] == version, f"{name}: image pins {version}, uv.lock has {lock[name]}"


def test_the_image_runs_the_local_python_minor_version():
    dockerfile = (ROOT / "sandbox" / "Dockerfile").read_text()
    [minor] = re.findall(r"^FROM python:(\d+\.\d+)-slim@sha256:[0-9a-f]{64}$", dockerfile, re.M)
    assert minor == f"{sys.version_info.major}.{sys.version_info.minor}"
    assert f"/python{minor}/site-packages/fourway/" in dockerfile


def test_sandboxed_evidence_never_matches_local_evidence():
    """The ledger answers "was this verified?" only for the environment that ran it."""
    image = "sha256:" + "ab" * 32
    assert ledger.env_digest(image) != ledger.env_digest()
    assert ledger.env_digest(image) != ledger.env_digest("sha256:" + "cd" * 32)


def test_model_scenarios_run_on_a_mined_pair_only_in_the_sandbox(monkeypatch):
    """Decision 0002 lifts for a mined pair only when its scenarios can't reach the host."""
    mined = next(c for c in load_corpus(CORPUS) if c.mined)
    reached = []

    class Recorder:
        def generate(self, ctx):
            reached.append(ctx)
            return generators.Scenarios({})  # no scenarios, so the fake sandbox never runs

    monkeypatch.setitem(generators.BLIND, "recorder", Recorder)
    with pytest.raises(ValueError, match="decision 0002"):
        bench.run([mined], "recorder")
    assert reached == []
    fake = runner.Sandbox("fourway-sandbox", "sha256:" + "ab" * 32)
    [result] = bench.run([mined], "recorder", sandbox=fake)
    assert len(reached) == 1 and result.verdict == "unverified"
    assert result.record["guards"]["env"] == ledger.env_digest(fake.image)


def test_pair_refuses_to_run_outside_the_sandbox_unless_trusted(tmp_path, monkeypatch, capsys):
    """Issue #2: scenarios from a diff someone else wrote must not run locally by default."""
    repo, base, a, b = make_pair(tmp_path, FLAGS, A_ON, B_ON)
    scenarios = tmp_path / "scenarios"
    scenarios.mkdir()
    (scenarios / "test_x.py").write_text("import fa\n\ndef test_x():\n    assert fa.ON in (True, False)\n")

    def unavailable(image):
        raise runner.SandboxError("no sandbox here")

    monkeypatch.setattr(runner.Sandbox, "resolve", unavailable)
    argv = ["pair", "--repo", str(repo), "--base", base, "--a", a, "--b", b, "--scenarios", str(scenarios)]
    assert cli.main(argv) == 2
    assert "--trusted" in capsys.readouterr().err
    assert cli.main([*argv, "--trusted"]) == 0


def test_the_sandbox_gives_the_local_outcomes(tmp_path, sandbox):
    """Run 4 compares against runs 1 to 3, which ran locally; the runner must not move the numbers."""
    repo, base, a, b = make_pair(tmp_path, FLAGS, A_ON, {**B_ON, "fb_new.py": "X = 1\n"})
    scenarios = {
        "test_a_breaks.py": "import fa\n\ndef test_flag_a_is_off():\n    assert not fa.ON\n",
        "test_b_module.py": "import fb_new\n\ndef test_b_module():\n    assert fb_new.X == 1\n",
        "test_broken.py": "import does_not_exist\n",
    }
    local = pipeline.verify(repo, base, a, b, scenarios, tmp_path / "local")
    boxed = pipeline.verify(repo, base, a, b, scenarios, tmp_path / "boxed", sandbox=sandbox)
    assert boxed.outcomes == local.outcomes
    assert boxed.findings == local.findings
    assert boxed.verdict == local.verdict == "regression"


def test_a_hang_in_the_sandbox_is_still_an_emergent_conflict(tmp_path, sandbox):
    repo, base, a, b = make_pair(tmp_path, FLAGS, A_ON, B_ON)
    scenario = "import time\nimport fa, fb\n\ndef test_finishes():\n    if fa.ON and fb.ON:\n        time.sleep(60)\n"
    result = pipeline.verify(
        repo, base, a, b, {"test_hang.py": scenario}, tmp_path / "run", timeout=8, sandbox=sandbox
    )
    [(test, outcomes)] = result.outcomes.items()
    assert outcomes == {"base": "passed", "a": "passed", "b": "passed", "ab": "timeout"}
    assert result.findings[test] == "emergent"


def test_a_broken_sandbox_stops_the_run_instead_of_scoring(tmp_path, sandbox):
    """If a missing image read as four crashed sessions, every pair would score as unverified and the
    run would look like a generator that writes broken scenarios."""
    repo, base, a, b = make_pair(tmp_path, FLAGS, A_ON, B_ON)
    gone = dataclasses.replace(sandbox, image="sha256:" + "0" * 64)
    with pytest.raises(runner.SandboxError):
        pipeline.verify(repo, base, a, b, {"test_x.py": "def test_x(): pass\n"}, tmp_path / "run", sandbox=gone)
