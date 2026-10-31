# 0003: The sandboxed runner is a Go binary that runs each pytest session in Docker

**Status:** accepted, 2026-10-31

## Context

[Decision 0002](0002-generated-scenarios-run-only-on-trusted-diffs.md)
requires a container with no network, no credentials, and a read-only copy of
the tree before fourway runs scenarios that a model wrote from a diff fourway
didn't author. Corpus v5 holds 76 clean pairs mined from real pull requests.
Their diffs are third-party input, so no generator can run on them until that
container exists, and run 4 needs them to reach the false-positive bar.

The owner chose Go for the runner on 2026-10-31. The project's earlier
recommendation kept Python for Phase 0 and named Go for this piece: a single
static binary installs next to a team's CI without a Python environment, and
the runner is the part that grows into container orchestration in Phase 1.

## Decision

- `sandbox/` is a Go module with no dependencies outside the standard
  library. Its binary, `fourway-sandbox`, runs one pytest session on one tree
  in one container by calling the `docker` CLI.
- The isolation policy lives only in the binary, in `dockerArgs`, so the
  Python side can't weaken it. Each session gets:
  - `--network none`, and `--pull never`, so a missing image fails instead of
    reaching a registry.
  - No host environment variables. The only variables set are `PYTHONPATH`,
    `PYTHONHASHSEED`, `PYTHONDONTWRITEBYTECODE`, `HOME=/tmp`, and the report
    path.
  - The tree mounted read-only, a read-only image filesystem, and a 256 MB
    tmpfs at `/tmp`.
  - User `nobody`, no capabilities, `no-new-privileges`, 512 processes, 2 GB
    of memory, and 2 CPUs.
- The session has no writable host mount. The plugin writes its report to the
  tmpfs, and the container prints it on stdout. The binary reads at most
  16 MB and accepts exactly one well-formed report; anything else counts as a
  crashed session.
- On a timeout the binary kills the container, not only the docker client.
- The image comes from `sandbox/Dockerfile`: the base is pinned by digest, and
  the test dependencies are hash-pinned from `uv.lock` by `uv export`. Python
  resolves the image tag to an ID once per run, every session runs that ID,
  and the evidence ledger's environment guard records it.
- A sandbox failure, such as Docker being down or the image missing, raises
  `SandboxError`. It's never a session outcome, so a broken sandbox can't read
  as a generator that writes broken scenarios.
- `bench --sandbox` lifts the mined-pair refusal. `pair` runs in the sandbox
  unless you pass `--trusted`, which closes issue #2. `check-corpus --sandbox`
  runs the upstream suites in the sandbox too.

## Consequences

Two behaviors differ from the local runner, and both are deliberate:

- A scenario that writes into the tree fails, and fails the same way on all
  four trees, so it reads as a broken scenario.
- Each repeat starts from a fresh container. State that one repeat leaves in
  the tree can no longer make a scenario flaky, which the local runner's
  flaky test relies on. Flakiness from timing or randomness still shows.

The image runs Python 3.12.13, and the development machine runs 3.12.16.
On 2026-10-31, every corpus v5 case passed `check-corpus --sandbox`, 88 of 88.
That pass alone proves little, because rule 7 ignores a test that fails the
same way on all four trees. So each case's suite also ran both ways, and the
outcomes were compared test by test: 86,660 test-tree outcomes, of which 28
differ. All 28 are one test, tomlkit's
`tests/test_toml_file.py::test_toml_file`, once in each of 28 tomlkit pairs.
It rewrites `tests/examples/example.toml` inside the tree, so it passes on all
four trees locally and fails on all four in the sandbox. Rule 7 ignores it,
so no case changes status, but tomlkit's sandboxed suite checks one test
fewer.

Container startup takes about 0.4 seconds on the development machine, and the
timeout covers it.

## Rejected

- **A Python wrapper around `docker run`.** It would be about as short. The
  owner chose Go for the install story and for Phase 1's orchestration.
- **The Docker Go SDK.** It brings a large dependency tree into a module that
  otherwise uses only the standard library. The CLI covers one container per
  session.
- **A writable output mount for the report.** A session could fill the host's
  disk through it, or plant a symlink that the host then follows.
- **gVisor (`runsc`) for Phase 0.** It isn't on the development machine. On
  Linux an ordinary container shares the host's kernel, so a kernel exploit
  escapes it. Before fourway runs on hosted infrastructure for other teams,
  sessions need a gVisor or microVM runtime, such as GKE Sandbox.
