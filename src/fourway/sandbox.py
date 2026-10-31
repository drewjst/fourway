"""Run pytest in a container: no network, no credentials, a read-only tree.

A scenario is code a model wrote after reading diffs and descriptions. When
those come from someone else, the scenario is untrusted code, so it runs here
instead of as a local subprocess. See docs/decisions/0003.

The container gets the tree and fourway's pytest plugin read-only, and a
scratch /tmp. Nothing from the host is writable inside it: the report comes
back on stdout. It gets no network, no Linux capabilities, the host user's ids
instead of root, limits on memory, CPU, and processes, and only the
environment variables pytest needs.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import threading
import uuid
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

from . import __version__

IMAGE_DIR = Path(__file__).parent / "sandbox_image"
PLUGIN_DIR = Path(__file__).parent  # the fourway package, for -p fourway.pytest_plugin

# Docker's own failures: the daemon refused, or the command couldn't start.
# pytest exits 0 to 5, so these never mean a test outcome.
_DOCKER_ERRORS = frozenset({125, 126, 127})

# The plugin writes the report to the container's /tmp and the shell prints
# it, so the container needs no writable host mount: none it could fill, and
# no report file it could swap for a symlink that the host would then follow.
# pytest's own output goes nowhere. The shell exits 0, so a non-zero status
# comes from Docker or from the container being killed.
_REPORT = "/tmp/fourway-report.json"
_SCRIPT = f'python -m pytest "$@" >/dev/null 2>&1; cat {_REPORT} 2>/dev/null; exit 0'
MAX_REPORT = 16 << 20  # far larger than a real report; a session that prints more is misbehaving
_MAX_STDERR = 64 << 10


class SandboxError(RuntimeError):
    """The sandbox can't run, so no outcome from it would mean anything."""


def default_image() -> str:
    """The image tag for the Dockerfile and requirements in this package, by content."""
    digest = hashlib.sha256()
    for name in ("Dockerfile", "requirements.txt"):
        digest.update((IMAGE_DIR / name).read_bytes())
    return f"fourway-sandbox:{digest.hexdigest()[:12]}"


def _docker(*args: str, timeout: float = 600.0) -> subprocess.CompletedProcess[str]:
    if shutil.which("docker") is None:
        raise SandboxError("docker is not installed; install it, or run only trusted changes without --sandbox")
    return subprocess.run(["docker", *args], capture_output=True, text=True, timeout=timeout)


def available() -> bool:
    """True if a Docker daemon answers."""
    try:
        return _docker("info", "--format", "{{.ServerVersion}}", timeout=30).returncode == 0
    except (SandboxError, subprocess.TimeoutExpired):
        return False


@dataclass(frozen=True)
class Sandbox:
    image: str = ""  # empty means default_image()
    memory: str = "2g"
    cpus: str = "2"
    pids: int = 512
    startup_slack: float = 15.0  # seconds added to each run's timeout for the container to start

    @property
    def tag(self) -> str:
        return self.image or default_image()

    def build(self) -> str:
        """Build the image from this package's Dockerfile. Pulls the pinned base image if needed."""
        proc = _docker("build", "--quiet", "-t", self.tag, str(IMAGE_DIR))
        if proc.returncode != 0:
            raise SandboxError(f"docker build failed: {proc.stderr.strip()}")
        return self.tag

    def ensure(self) -> None:
        """Raise SandboxError unless Docker answers and the image exists."""
        if not available():
            raise SandboxError("the Docker daemon is not running; start it, or run only trusted changes")
        if _docker("image", "inspect", self.tag).returncode != 0:
            raise SandboxError(f"image {self.tag} is missing; run `fourway sandbox build`")

    @cached_property
    def image_id(self) -> str:
        proc = _docker("image", "inspect", "--format", "{{.Id}}", self.tag)
        if proc.returncode != 0:
            raise SandboxError(f"image {self.tag} is missing; run `fourway sandbox build`")
        return proc.stdout.strip()

    def env_digest(self) -> str:
        """The evidence ledger's environment guard: the image recipe that ran the tests.

        The tag, not the image id: the recipe pins the base image by digest and
        every package by hash, and a rebuild changes only build timestamps,
        which would otherwise make the same environment look new.
        """
        body = json.dumps({"image": self.tag, "fourway": __version__}, sort_keys=True).encode()
        return "sha256:" + hashlib.sha256(body).hexdigest()

    def command(self, tree: Path, pythonpath: tuple[str, ...], pytest_args: list[str]) -> tuple[str, list[str]]:
        """Return a container name and the `docker run` argv for one pytest run in ``tree``."""
        name = f"fourway-{uuid.uuid4().hex[:12]}"
        work = "/work/tree"
        env = {
            # fourway's package comes first, so a tree can't shadow the plugin.
            "PYTHONPATH": ":".join(["/opt/fourway", work, *(f"{work}/{p}" for p in pythonpath)]),
            "PYTHONHASHSEED": "0",
            "PYTHONDONTWRITEBYTECODE": "1",
            "HOME": "/tmp",
            "FOURWAY_REPORT": _REPORT,
        }
        argv = [
            "docker", "run", "--rm", "--name", name,
            "--network", "none",
            "--read-only", "--tmpfs", "/tmp",
            "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--user", f"{os.getuid()}:{os.getgid()}",
            "--memory", self.memory, "--cpus", self.cpus, "--pids-limit", str(self.pids),
            "--volume", f"{tree.resolve()}:{work}:ro",
            "--volume", f"{PLUGIN_DIR.resolve()}:/opt/fourway/fourway:ro",
            "--workdir", work,
            *(arg for key, value in env.items() for arg in ("--env", f"{key}={value}")),
            self.tag, "sh", "-c", _SCRIPT, "fourway-run", *pytest_args,
        ]
        return name, argv

    def run(self, tree: Path, pythonpath: tuple[str, ...], report: Path, pytest_args: list[str], timeout: float) -> bool:
        """Run pytest in a container and write its report to ``report``.

        Return False if it timed out; raise SandboxError if Docker failed. When
        the session printed no valid report, ``report`` is not written, and the
        runner reads the run as crashed. The container can't reach ``report``
        or any other host file, so a scenario in one tree can't touch another
        tree's report.
        """
        name, argv = self.command(tree, pythonpath, pytest_args)
        try:
            code, out, err = _run_capped(argv, timeout + self.startup_slack)
        except subprocess.TimeoutExpired:
            # Killing the docker client leaves the container running.
            subprocess.run(["docker", "rm", "--force", name], capture_output=True)
            return False
        if code in _DOCKER_ERRORS:
            raise SandboxError(f"docker run failed ({code}): {err.decode(errors='replace').strip()[-500:]}")
        data = parse_report(out)
        if data is not None:
            report.write_text(json.dumps(data))
        return True


def parse_report(out: bytes | None) -> dict | None:
    """The plugin's report from a session's stdout, or None.

    The session controls these bytes. Anything but exactly one report with
    the plugin's fields and types counts as no report: None from an overflow,
    nothing, a truncated report, or a forged one printed next to the real one.
    """
    if not out:
        return None
    try:
        data = json.loads(out)
    except ValueError:
        return None
    ok = (
        isinstance(data, dict)
        and set(data) == {"tests", "collect_errors", "exitstatus"}
        and isinstance(data["tests"], dict)
        and all(isinstance(t, str) and isinstance(o, str) for t, o in data["tests"].items())
        and isinstance(data["collect_errors"], list)
        and all(isinstance(e, str) for e in data["collect_errors"])
        and type(data["exitstatus"]) is int
    )
    return data if ok else None


def _run_capped(argv: list[str], timeout: float) -> tuple[int, bytes | None, bytes]:
    """Run ``argv``; return its status, stdout (None past MAX_REPORT bytes), and the start of stderr.

    The session can print without limit, so neither stream is held in full.
    Raises TimeoutExpired after killing the process.
    """
    kept: dict[str, tuple[bytes, bool]] = {}

    def drain(key: str, stream, limit: int) -> None:
        chunks, size = [], 0
        while chunk := stream.read(65536):
            size += len(chunk)
            if size <= limit:
                chunks.append(chunk)
        kept[key] = (b"".join(chunks), size > limit)

    with subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
        threads = [
            threading.Thread(target=drain, args=("out", proc.stdout, MAX_REPORT)),
            threading.Thread(target=drain, args=("err", proc.stderr, _MAX_STDERR)),
        ]
        for t in threads:
            t.start()
        try:
            proc.wait(timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            raise
        finally:
            for t in threads:
                t.join()
    out, overflow = kept["out"]
    return proc.returncode, None if overflow else out, kept["err"][0]
