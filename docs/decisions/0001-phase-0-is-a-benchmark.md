# 0001: Phase 0 is a benchmark, not a tool

**Status:** accepted, 2026-10-30

## Context

The claim behind fourway is that generated scenarios, run on base, A, B, and
the merge, catch semantic conflicts that existing tests miss. The published
evidence is thin. SAM, the closest prior work, detected 9 of 29 semantic
conflicts in its best configuration. A 2026 follow-up found that no single
language model beat the traditional test generators; only ensembles did.
Nobody has published how often cleanly merging pairs of agent changes
conflict semantically.

A pull-request integration built before a recall number exists would measure
nothing and could not be trusted.

## Decision

Phase 0 builds only what measures recall, false positives, and cost per pair:

- A seeded corpus of pairs with known answers. Each conflict case has a clean
  twin that differs in one side, so a generator cannot score by pattern
  matching on the files a pair touches.
- The four-way runner, the classifier, and the evidence ledger.
- Control generators that prove the score can come out wrong.

The bar for moving past Phase 0 is at least 50% recall on seeded conflicts,
under 5% false positives on clean pairs, and under $5 per pair.

## Rejected

- **Start with the GitHub App.** There is no recall number to put behind it.
- **Start with SAM's Java dataset.** It needs a Maven toolchain and Java test
  generation; the first generator targets Python. It stays a later corpus
  source.
- **Report recall as a bare percentage.** With six cases, 3/3 has a 95%
  interval of 44% to 100%. Reports show counts and Wilson intervals.
