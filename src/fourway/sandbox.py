"""Run pytest in a container: no network, no credentials, a read-only tree.

A scenario is code a model wrote after reading diffs and descriptions. When
those come from someone else, the scenario is untrusted code, so it runs here
instead of as a local subprocess. See docs/decisions/0003.

The container gets the tree read-only, a scratch /tmp, the directory the
report goes to, and fourway's pytest plugin, also read-only. It gets no
network, no Linux capabilities, the host user's ids instead of root, limits on
memory, CPU, and processes, and only the environment variables pytest needs.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
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

    def command(self, tree: Path, pythonpath: tuple[str, ...], report: Path, pytest_args: list[str]) -> tuple[str, list[str]]:
        """Return a container name and the `docker run` argv for one pytest run in ``tree``.

        ``report.parent`` is mounted writable, so it must hold nothing but this run's report.
        """
        name = f"fourway-{uuid.uuid4().hex[:12]}"
        work = "/work/tree"
        env = {
            # fourway's package comes first, so a tree can't shadow the plugin.
            "PYTHONPATH": ":".join(["/opt/fourway", work, *(f"{work}/{p}" for p in pythonpath)]),
            "PYTHONHASHSEED": "0",
            "PYTHONDONTWRITEBYTECODE": "1",
            "HOME": "/tmp",
            "FOURWAY_REPORT": f"/report/{report.name}",
        }
        argv = [
            "docker", "run", "--rm", "--name", name,
            "--network", "none",
            "--read-only", "--tmpfs", "/tmp",
            "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--user", f"{os.getuid()}:{os.getgid()}",
            "--memory", self.memory, "--cpus", self.cpus, "--pids-limit", str(self.pids),
            "--volume", f"{tree.resolve()}:{work}:ro",
            "--volume", f"{report.parent.resolve()}:/report",
            "--volume", f"{PLUGIN_DIR.resolve()}:/opt/fourway/fourway:ro",
            "--workdir", work,
            *(arg for key, value in env.items() for arg in ("--env", f"{key}={value}")),
            self.tag, "python", "-m", "pytest", *pytest_args,
        ]
        return name, argv

    def run(self, tree: Path, pythonpath: tuple[str, ...], report: Path, pytest_args: list[str], timeout: float) -> bool:
        """Run pytest in a container and leave its report at ``report``.

        Return False if it timed out; raise SandboxError if Docker failed. Each
        run writes into a directory of its own, so a scenario in one tree can't
        overwrite another tree's report.
        """
        with tempfile.TemporaryDirectory(dir=report.parent, prefix=".sandbox-") as own:
            own_report = Path(own) / "report.json"
            name, argv = self.command(tree, pythonpath, own_report, pytest_args)
            try:
                proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout + self.startup_slack)
            except subprocess.TimeoutExpired:
                # Killing the docker client leaves the container running.
                subprocess.run(["docker", "rm", "--force", name], capture_output=True)
                return False
            if proc.returncode in _DOCKER_ERRORS and not own_report.exists():
                raise SandboxError(f"docker run failed ({proc.returncode}): {proc.stderr.strip()[-500:]}")
            if own_report.is_file():
                own_report.replace(report)
        return True
