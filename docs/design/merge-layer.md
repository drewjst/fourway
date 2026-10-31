# Design note: the merge layer

**Status:** proposal, 2026-10-30. Not a decision. Nothing here is scheduled,
and Phase 0's bar in [decision 0001](../decisions/0001-phase-0-is-a-benchmark.md)
still gates everything after it.

## Summary

Fourway can grow from a conflict detector into the layer that decides which
agent changes land together. It doesn't replace Git. Git keeps storing the
code; fourway adds what Git has no concept of: what each change is for, what
it relies on, and evidence that it still works alongside everything else that
landed with it.

## Two problems called "source control for agents"

Agents raise the number of concurrent changes to a repository. Anthropic
reported that its merges went from about 2,500 a day in May 2026 to more than
30,000 a day in September
([Redesigning source control for the age of agents](https://www.anthropic.com/research/redesigning-source-control)).
That volume causes two separate problems:

- **Storage and throughput**: objects, locks, checkouts, and merges per
  second. Anthropic solved this with a bespoke system. Below that scale, Git
  handles the load, and every CI system, editor, code host, and agent already
  works with Git.
- **Semantics**: two changes that are each correct and merge cleanly can still
  break together. Git checks that text merges. Nothing checks that behavior
  survives the merge.

Fourway addresses only the second problem.

## From three-way to four-way

Git's merge is three-way. It compares text across the base, one side, and the
other side, and it reports a conflict when both sides edit the same lines.

Fourway's check is four-way. It runs scenario tests on the base, change A,
change B, and the merged result, and it reports a conflict when the merge
loses behavior that A or B had. The result is a failing test that either
author can run, not a set of conflict markers.

## Layers

The merge layer has the following parts, from the bottom up:

| Layer | What it does | Built |
|---|---|---|
| Storage | Holds the code. This layer is Git, unchanged. | Git |
| Change record | Records each change's intent, the base it started from, the interfaces it relies on, and its external effects, such as migrations. The record lives in Git refs so it moves with the repository. | No |
| Interaction graph | Finds which in-flight changes could interact through shared symbols, call paths, or invariants. Changes that can't interact land together without pairwise checks. | No |
| Verifier | Runs four-way scenarios on each pair that could interact. A conflict returns a runnable reproduction to the change that needs to revise. | Phase 0 |
| Invariant suite | Keeps scenarios that caught a real conflict, or that the team approved, as permanent tests. Every batch runs them with no model calls. | No |
| Evidence ledger | Records which exact combination of commits, environment, and scenarios was verified, and invalidates the record when any of those inputs change. | Phase 0 |
| Agent API | Lets agents submit a change, ask which in-flight changes touch a symbol, ask whether a combination was verified, and fetch the reproduction for a rejected change. Served over MCP. | No |

## What changes for an agent

An agent that works through the merge layer sees the following differences
from working with Git branches:

- A conflict arrives as a failing test with a reproduction, not as conflict
  markers.
- A change is verified again only when something it relies on changes, not
  whenever any commit lands.
- The merge layer handles rebasing. Textual conflicts go to an agent to
  resolve. Semantic conflicts go back to the change's author, along with the
  other change's intent.
- If a change ran a migration or another external effect, reverting it runs
  the recorded compensation as well as reverting the code.

## Where it runs

A team uses one of two insertion points, and the deliverable is the same in
both:

- **Before merge**: the merge layer runs where a merge queue runs. It verifies
  interacting pairs before either one lands.
- **Before deploy**: changes merge first, and the merge layer verifies each
  batch that landed together before it deploys. Anthropic dropped its merge
  queue for this model at agent scale. The batch also tells fourway exactly
  which changes landed together, which makes pair selection more precise.

## Cost at scale

The number of pairs grows with the square of the number of changes in flight.
Generating scenarios for every pair is affordable for a team with a few
concurrent changes and unaffordable at agent scale. Two layers keep the cost
bounded:

- The interaction graph removes pairs that can't interact before any
  scenario is generated.
- The invariant suite covers known classes of interaction without model
  calls, so generation is reserved for interactions the suite hasn't seen.

Without both, cost per batch grows quadratically.

## Build order

Each phase is useful on its own, and each has a gate to pass before the next
phase starts:

1. **Phase 0, the detector**: the benchmark in this repository. Gate: at
   least 50% recall on seeded conflicts, under 5% false positives on clean
   pairs, and under $5 per pair.
2. **Phase 1, a pair verifier on real repositories**: runs in a sandbox next
   to a team's existing CI and merge queue, on historical and live pairs.
   Gate: it catches a conflict that the team's CI and review missed.
3. **Phase 2, the merge layer**: adds the interaction graph, batching, the
   invariant suite, and both insertion points. Gate: a false-positive bar
   stricter than Phase 0's, set before anything is measured.
4. **Phase 3, change records and the agent API**: records intent,
   dependencies, and effects for every change, and serves them to agents.

## Non-goals

- **Replacing Git's storage.** Only a team at Anthropic's scale needs it, and
  a team that large builds its own.
- **Resolving textual conflicts.** Agents already resolve them well. The
  merge layer routes them to an agent and doesn't add its own resolver.
- **Detecting every behavioral conflict.** Fourway finds conflicts that a
  generated or kept scenario exercises. A pair with no usable scenario is
  `unverified`, never `clean`.

## Risks

- **False positives cost more here.** A standalone verifier that flags a
  clean pair costs a reviewer a minute. A merge layer that flags a clean pair
  blocks a merge, and teams turn off a tool that blocks good changes. This
  is why Phase 2's bar is stricter than Phase 0's.
- **Generated scenarios are untrusted code.** A merge layer runs scenarios
  generated from other people's diffs. [Decision 0002](../decisions/0002-generated-scenarios-run-only-on-trusted-diffs.md)
  requires a sandboxed runner before fourway accepts any diff it didn't
  author, so Phase 1 depends on that runner.
- **Flaky scenarios read as conflicts.** The runner already repeats each
  scenario and excludes ones whose outcome changes. A merge layer needs the
  same rule on every batch.
- **The suite pays off only if conflicts repeat.** The invariant suite lowers
  cost only if conflicts fall into recurring classes, such as retries and
  idempotency, or caches and invalidation. Phase 1 needs to measure how often
  they do.

## Open questions

- How the interaction graph finds pairs that share an invariant but no
  symbol, such as two changes that both affect how often a customer is
  charged.
- Where a change record lives so that agents, CI, and the code host can all
  read it: Git refs, Git notes, or a service beside the repository.
- How a compensation for an external effect is recorded and tested, given
  that it runs only when something has already gone wrong.
