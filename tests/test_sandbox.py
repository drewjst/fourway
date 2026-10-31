"""The sandbox must contain what a model-written scenario can do: no network, no secrets, no writes to the tree.

Each probe is a scenario that passes only if the sandbox stopped it, so a hole
in the sandbox shows up as a failed scenario. Each probe is also run against a
sandbox with that one hole opened, to show it can fail.
"""

import dataclasses
import re
import subprocess
from importlib.metadata import version
from pathlib import Path

import pytest

from fourway import runner
from fourway import sandbox as sb
from fourway.cli import main
from fourway.sandbox import Sandbox, SandboxError

needs_docker = pytest.mark.skipif(not sb.available(), reason="needs a running Docker daemon")

SECRET = "sk-ant-fourway-test-not-a-key"

NETWORK = '''
import socket


def test_no_connection():
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=3)
    except OSError:
        return
    raise AssertionError("reached the network")


def test_no_name_resolution():
    try:
        socket.getaddrinfo("example.com", 443)
    except OSError:
        return
    raise AssertionError("resolved a name")
'''

WRITES = '''
from pathlib import Path


def test_cannot_write_the_tree():
    try:
        Path("planted.py").write_text("x = 1")
    except OSError:
        return
    raise AssertionError("wrote into the tree")


def test_can_write_tmp(tmp_path):
    (tmp_path / "scratch").write_text("ok")
'''

HOST = f'''
import os
from pathlib import Path


def test_no_secrets_in_the_environment():
    assert {SECRET!r} not in os.environ.values()
    assert "ANTHROPIC_API_KEY" not in os.environ
    assert os.environ["HOME"] == "/tmp"


def test_host_files_are_absent():
    assert not Path({str(Path.home())!r}).exists()
    assert not Path({str(Path(__file__).resolve())!r}).exists()


def test_not_root():
    assert os.getuid() != 0
'''


@dataclasses.dataclass(frozen=True)
class Weakened(Sandbox):
    """The sandbox with one protection removed, to show the probe for it can fail."""

    hole: str = ""

    def command(self, *args):
        name, argv = super().command(*args)
        if self.hole == "network":
            at = argv.index("--network")
            del argv[at:at + 2]
        elif self.hole == "writable tree":
            argv = [arg.removesuffix(":ro") if arg.endswith(":/work/tree:ro") else arg for arg in argv]
        elif self.hole == "host environment":
            at = argv.index(self.tag)
            argv[at:at] = ["--env", "ANTHROPIC_API_KEY"]  # no value: Docker passes the host's through
        return name, argv


@pytest.fixture(scope="module")
def box():
    box = Sandbox()
    box.build()  # cached layers make a rebuild take seconds
    return box


@pytest.fixture(autouse=True)
def secret(monkeypatch):
    """The generator's API key sits in fourway's environment during a run; plant a fake one."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", SECRET)


def probe(box, tmp_path, source, timeout=60.0):
    tree = tmp_path / "tree"
    tree.mkdir(parents=True)
    runner.install_scenarios(tree, {"test_probe.py": source})
    (tmp_path / "reports").mkdir(exist_ok=True)
    report = runner.run_pytest(tree, runner.SCENARIO_DIR, tmp_path / "reports" / "probe.json", timeout, sandbox=box)
    return tree, {test.split("::")[-1]: outcome for test, outcome in report.outcomes.items()}, report


@needs_docker
def test_outcomes_match_a_local_run(box, tmp_path):
    """The sandbox changes where tests run, not what they find."""
    source = "def test_passes():\n    assert 1 + 1 == 2\n\n\ndef test_fails():\n    assert 1 + 1 == 3\n"
    _, sandboxed, _ = probe(box, tmp_path / "boxed", source)
    _, local, _ = probe(None, tmp_path / "local", source)
    assert sandboxed == local == {"test_passes": "passed", "test_fails": "failed"}


@needs_docker
def test_the_network_is_unreachable(box, tmp_path):
    """A prompt-injected scenario must not be able to send anything anywhere."""
    _, outcomes, _ = probe(box, tmp_path, NETWORK)
    assert outcomes == {"test_no_connection": "passed", "test_no_name_resolution": "passed"}


@needs_docker
def test_the_tree_is_read_only_and_tmp_is_writable(box, tmp_path):
    """A scenario must not plant code in the tree that a later run, or the host, would pick up."""
    tree, outcomes, _ = probe(box, tmp_path, WRITES)
    assert outcomes == {"test_cannot_write_the_tree": "passed", "test_can_write_tmp": "passed"}
    assert not (tree / "planted.py").exists()


@needs_docker
def test_no_secret_or_host_file_reaches_the_scenario(box, tmp_path):
    """The generator's API key lives in this process's environment; a scenario must never see it."""
    _, outcomes, _ = probe(box, tmp_path, HOST)
    assert outcomes == dict.fromkeys(
        ["test_no_secrets_in_the_environment", "test_host_files_are_absent", "test_not_root"], "passed"
    )


@needs_docker
@pytest.mark.parametrize("hole, source, test", [
    ("writable tree", WRITES, "test_cannot_write_the_tree"),
    ("host environment", HOST, "test_no_secrets_in_the_environment"),
    ("network", NETWORK, "test_no_name_resolution"),
])
def test_each_probe_fails_when_its_hole_is_open(box, tmp_path, hole, source, test):
    """A probe that passes whatever the sandbox does would prove nothing."""
    _, outcomes, _ = probe(Weakened(hole=hole), tmp_path, source)
    if hole == "network" and outcomes[test] == "passed":
        pytest.skip("this machine has no network, so an open network can't be told from a closed one")
    assert outcomes[test] == "failed"


@needs_docker
def test_a_scenario_cannot_touch_another_trees_report(box, tmp_path):
    """The four trees run at once; one tree's scenario must not rewrite the outcomes another tree reports."""
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports" / "base-0.json").write_text('{"tests": {"t": "passed"}, "collect_errors": []}')
    _, outcomes, _ = probe(box, tmp_path, '''
import os
from pathlib import Path


def test_cannot_see_other_reports():
    assert os.listdir(Path(os.environ["FOURWAY_REPORT"]).parent) == []
''')
    assert outcomes == {"test_cannot_see_other_reports": "passed"}


@dataclasses.dataclass(frozen=True)
class Named(Sandbox):
    """Records each container name, so a test can look for its own container among others."""

    names: list = dataclasses.field(default_factory=list)

    def command(self, *args):
        name, argv = super().command(*args)
        self.names.append(name)
        return name, argv


@needs_docker
def test_a_timeout_stops_the_container(box, tmp_path):
    """Killing the docker client leaves the container running unless fourway removes it."""
    quick = Named(startup_slack=0)
    _, _, report = probe(quick, tmp_path, "import time\n\n\ndef test_hang():\n    time.sleep(300)\n", timeout=8)
    assert report.crashed == "timeout"
    [name] = quick.names
    left = subprocess.run(
        ["docker", "ps", "--all", "--quiet", "--filter", f"name=^{name}$"], capture_output=True, text=True
    ).stdout
    assert left.strip() == ""


@needs_docker
def test_a_docker_failure_is_an_error_not_an_outcome(tmp_path):
    """If Docker can't start the container, no test ran; reading that as "error" outcomes would score it."""
    with pytest.raises(SandboxError, match="docker run failed"):
        probe(Sandbox(image="fourway-sandbox:no-such-image"), tmp_path, "def test_x():\n    pass\n")


def test_the_sandbox_runs_the_same_pytest_as_the_host():
    """A different pytest in the container would make sandboxed and local scores incomparable."""
    pins = dict(re.findall(r"^([a-z][a-z0-9-]*)==([^\s\\]+)", (sb.IMAGE_DIR / "requirements.txt").read_text(), re.M))
    for package in ("pytest", "pluggy", "typeguard", "click"):
        assert pins[package] == version(package), package


def test_the_image_tag_follows_the_recipe(tmp_path, monkeypatch):
    """Evidence is keyed on the tag, so any change to the Dockerfile or the pins must change it."""
    for name in ("Dockerfile", "requirements.txt"):
        (tmp_path / name).write_bytes((sb.IMAGE_DIR / name).read_bytes())
    monkeypatch.setattr(sb, "IMAGE_DIR", tmp_path)
    before = sb.default_image()
    (tmp_path / "requirements.txt").write_text((tmp_path / "requirements.txt").read_text() + "\n")
    assert sb.default_image() != before


def test_pair_refuses_to_run_unsandboxed_unless_trusted(tmp_path, monkeypatch, capsys):
    """Decision 0002: scenarios on changes someone else wrote run only in the sandbox."""
    monkeypatch.setattr(sb, "available", lambda: False)
    scenarios = tmp_path / "scenarios"
    scenarios.mkdir()
    (scenarios / "test_x.py").write_text("def test_x():\n    pass\n")
    assert main(["pair", "--repo", str(tmp_path), "--base", "main", "--a", "a", "--b", "b",
                 "--scenarios", str(scenarios)]) == 2
    assert "--trusted" in capsys.readouterr().err
