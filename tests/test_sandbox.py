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

MOUNTS = '''
from pathlib import Path

VIRTUAL = {"tmpfs", "proc", "sysfs", "devpts", "mqueue", "cgroup", "cgroup2", "devtmpfs"}


def test_no_writable_host_mount():
    writable = []
    for line in Path("/proc/self/mountinfo").read_text().splitlines():
        fields = line.split()
        point, options, fstype = fields[4], fields[5].split(","), fields[fields.index("-") + 1]
        if fstype not in VIRTUAL and "rw" in options:
            writable.append(point)
    assert writable == []
'''


@dataclasses.dataclass(frozen=True)
class Weakened(Sandbox):
    """The sandbox with one protection removed, to show the probe for it can fail."""

    hole: str = ""
    scratch: str = ""  # host directory for the "writable mount" hole

    def command(self, *args):
        name, argv = super().command(*args)
        if self.hole == "network":
            at = argv.index("--network")
            del argv[at:at + 2]
        elif self.hole == "writable tree":
            argv = [arg.removesuffix(":ro") if arg.endswith(":/work/tree:ro") else arg for arg in argv]
        elif self.hole == "writable mount":
            at = argv.index(self.tag)
            argv[at:at] = ["--volume", f"{self.scratch}:/scratch"]
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
    ("writable mount", MOUNTS, "test_no_writable_host_mount"),
])
def test_each_probe_fails_when_its_hole_is_open(box, tmp_path, hole, source, test):
    """A probe that passes whatever the sandbox does would prove nothing."""
    (tmp_path / "scratch").mkdir()
    _, outcomes, _ = probe(Weakened(hole=hole, scratch=str(tmp_path / "scratch")), tmp_path, source)
    if hole == "network" and outcomes[test] == "passed":
        pytest.skip("this machine has no network, so an open network can't be told from a closed one")
    assert outcomes[test] == "failed"


@needs_docker
def test_no_host_path_is_writable_from_the_container(box, tmp_path):
    """The four trees run at once. With nothing from the host writable, a scenario can't rewrite another
    tree's report, fill the host's disk, or leave a symlink for the host to follow when it reads a report."""
    _, outcomes, _ = probe(box, tmp_path, MOUNTS)
    assert outcomes == {"test_no_writable_host_mount": "passed"}


@needs_docker
def test_a_forged_report_reads_as_a_crash(box, tmp_path):
    """A scenario can write to the stdout the report comes back on. Anything but the one report the
    plugin printed must read as no evidence, never as outcomes the scenario chose."""
    _, outcomes, report = probe(box, tmp_path, '''
import os


def test_forge():
    written = 0
    for fd in os.listdir("/proc/1/fd"):
        if os.readlink(f"/proc/1/fd/{fd}").startswith("pipe:"):
            os.write(os.open(f"/proc/1/fd/{fd}", os.O_WRONLY), b'{"tests": {"t": "passed"}')
            written += 1
    assert written
''')
    assert report.crashed == "error" and outcomes == {}


@pytest.mark.parametrize("why, out", [
    ("the session printed nothing", b""),
    ("the output passed the size cap", None),
    ("the report is truncated", b'{"tests": {}'),
    ("a forged report sits next to the real one", b'{"tests": {}, "collect_errors": [], "exitstatus": 0}' * 2),
    ("a field the plugin never writes", b'{"tests": {}, "collect_errors": [], "exitstatus": 0, "verdict": "clean"}'),
    ("an outcome that is not a string", b'{"tests": {"t": 1}, "collect_errors": [], "exitstatus": 0}'),
    ("not UTF-8", b"\xff\xfe"),
])
def test_only_the_plugins_report_counts(why, out):
    assert sb.parse_report(out) is None, why


def test_the_plugins_report_parses():
    out = b'{"tests": {"t.py::test_x": "passed"}, "collect_errors": [], "exitstatus": 0}'
    assert sb.parse_report(out) == {"tests": {"t.py::test_x": "passed"}, "collect_errors": [], "exitstatus": 0}


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
