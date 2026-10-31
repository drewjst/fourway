# 0003: Scenarios on third-party changes run in a container

**Status:** accepted, 2026-10-31. It meets the condition that
[decision 0002](0002-generated-scenarios-run-only-on-trusted-diffs.md) set
before fourway accepts a change it didn't write. Amended 2026-10-31: the
report comes back on stdout, so nothing from the host is writable in the
container.

## Context

Decision 0002 limited generated scenarios to changes this project wrote until
the runner executes them in a container with no network, no credentials, and
a read-only copy of the tree. Corpus v5 holds 76 clean pairs mined from other
people's pull requests, so the false-positive rate can't be measured on them
until that container exists. The owner chose a Docker sandbox over amending
0002 on 2026-10-31.

## Decision

With `--sandbox`, fourway runs each tree's pytest run with `docker run`, in an
image built from `src/fourway/sandbox_image/`. The container has the following
limits:

- No network: `--network none`.
- No Linux capabilities, no privilege escalation, and the host user's ids
  instead of root.
- A read-only root filesystem and a read-only tree. The only writable place
  is a scratch `/tmp`. The plugin writes its report there, and the container
  prints it on stdout. fourway reads at most 16 MB and accepts exactly one
  report with the plugin's fields; anything else reads as a crashed run.
  Nothing from the host is writable, so a scenario can't rewrite another
  tree's report, fill the host's disk, or leave a symlink in place of its
  report for the host to follow.
- No environment from the host. The container gets `PYTHONPATH`,
  `PYTHONHASHSEED`, `PYTHONDONTWRITEBYTECODE`, `HOME=/tmp`, and
  `FOURWAY_REPORT`, plus the base image's own variables, such as `PATH`.
- At most 2 GB of memory, 2 CPUs, and 512 processes.
- fourway's own package, mounted read-only, for its pytest plugin. It comes
  first on `PYTHONPATH`, so a tree can't shadow the plugin by accident.

The image pins its base by digest and every package by hash, at the versions
the host runs; a test checks that pytest, pluggy, typeguard, and click match.
The image tag is a hash of the recipe, and the evidence ledger records that
tag as the environment of a sandboxed run.

`fourway bench` refuses model-written scenarios on mined pairs without
`--sandbox`. `fourway pair` runs in the sandbox unless `--trusted` is passed.
If Docker can't start a container, the run stops with `SandboxError` instead
of recording error outcomes. A run that times out has its container removed.

`tests/test_sandbox.py` probes each protection with a scenario that passes
only if the sandbox stopped it. Each probe also runs against a sandbox with
that one protection removed, and fails there.

## Limits

- The sandbox contains a scenario. It doesn't make the scenario's verdict
  trustworthy. A scenario runs in the same pytest process as fourway's
  plugin, so it can falsify the outcomes for its own tree, which a
  prompt-injected scenario could also do by asserting the wrong thing.
- On Linux, containers share the host's kernel, so a kernel exploit escapes.
  On macOS, Docker Desktop runs containers in a virtual machine. A gVisor or
  microVM runtime would be stronger.
- The Docker daemon is trusted, and anyone who runs fourway can run
  containers.
- A test that writes into its tree fails in the sandbox. On 2026-10-31, every
  corpus v5 case's suite ran both locally and in the sandbox, and the outcomes
  were compared test by test: 86,660 test-tree outcomes, of which 28 differ.
  All 28 are tomlkit's `tests/test_toml_file.py::test_toml_file`, once in each
  of 28 tomlkit pairs. It rewrites `tests/examples/example.toml`, so it passes
  on all four trees locally and fails on all four in the sandbox. All 88 cases
  pass `check-corpus --sandbox` anyway, because check rule 7 ignores a test
  that fails alike on all four trees, so that pass alone can't show this
  difference. tomlkit's sandboxed suite checks one test fewer than its local
  one.
- `check-corpus` runs the upstream suites outside the sandbox unless
  `--sandbox` is passed. The owner approved running those suites locally on
  2026-10-30 and 2026-10-31.

## Rejected

- **Porting the runner to Go first.** Issue #2 recommended Go for the
  sandboxed runner. The container is what protects the host, and the language
  that starts it doesn't change that. A Go runner stays an option for when a
  single installable binary matters.
- **A writable directory for each run's report.** The first version of this
  decision mounted one. A scenario could fill the host's disk through it, or
  replace its report with a symlink to a host file, which fourway then read.
- **A virtual machine per run.** It's stronger than a container, but a
  four-way run needs four of them per pair, and it adds a dependency that the
  development machine and CI don't have.
- **Amending decision 0002 to trust merged pull requests.** A merged pull
  request's description is still text from outside the project, and the
  generator reads it.
