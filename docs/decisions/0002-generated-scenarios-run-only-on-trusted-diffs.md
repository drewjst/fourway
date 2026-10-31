# 0002: Generated scenarios run only on trusted diffs until the runner is sandboxed

**Status:** accepted, 2026-10-30. [Decision 0003](0003-scenarios-on-third-party-changes-run-in-a-container.md)
meets its condition with the `--sandbox` runner, 2026-10-31.

## Context

A scenario is Python that a model writes after reading two diffs and two
change descriptions. Fourway then executes it. When the diff comes from
someone else, such as a public pull request, the diff is attacker-controlled
input to the model, and a prompt injection in it can steer the model into
writing a test that does anything the runner's user can do.

Making scenarios declarative would remove that path, but the scenario is the
product: a runnable reproduction an agent can act on.

## Decision

- Phase 0 runs scenarios as local subprocesses, and only on the seeded corpus,
  whose diffs we wrote.
- The runner passes a minimal environment: `PATH`, `HOME`, and fixed Python
  settings. It does not pass other environment variables or credentials.
- Before fourway accepts a diff it did not author, the runner must execute
  scenarios in a container with no network, no credentials, and a read-only
  copy of the tree. That work is tracked as a GitHub issue.

## Rejected

- **Declarative scenarios.** They remove the runnable reproduction, which is
  the deliverable.
- **Trusting the local runner with a filtered environment.** A filtered
  environment still leaves the user's files and network reachable.
