# Run 3: Claude Opus 5.5 on corpus v3

**Date:** 2026-10-30 · **Generator:** `claude`, `claude-opus-5-5`, effort `high`,
one generation per pair · **Test repeats:** 3 · **Commit:** `9ef719a`

Corpus v3 adds six cases seeded into pinned commits of `cachetools`,
`tenacity`, and `tinydb`. The six toy cases are the same as in corpus v2.

| Measure | All cases | Toy cases | Real-repository cases |
|---|---|---|---|
| Recall | 6/6 (95% CI 61% to 100%) | 3/3 | 3/3 |
| False positives | 1/6 (95% CI 3% to 56%) | 1/3 | 0/3 |
| Generator errors | 0/12 | 0/6 | 0/6 |
| Fallbacks | 0/12 | 0/6 | 0/6 |
| Cost per pair | $0.24 | $0.08 | $0.39 (at most $0.50) |

The run cost $2.82 in total. Real-repository prompts were 59,000 to 92,000
input tokens. Output was 1,851 to 6,784 tokens per pair.

## Detections

Each detection names the seeded mechanism in its rationale:

- `cachetools-mru-x-fast-get`: B's `get()` skips `__getitem__` for every class
  it didn't update, so `MRUCache.get()` stops counting as a use. Three
  `differential_a` findings.
- `tenacity-idle-budget-x-stop-first`: B runs the stop strategy before the
  wait, so `stop_before_idle` reads a stale `upcoming_sleep` and overruns the
  budget. Four `differential_a` findings.
- `tinydb-warm-cache-x-ordered-search`: A appends an inserted document to
  cached results, so a cached search loses B's ID order. Two `differential_b`
  and two emergent findings. The emergent ones check that a cached search
  matches a fresh one.
- `retry-x-nonce-key`, `cache-x-set-price`, and `receipt-x-event-rename`: the
  same mechanisms as in runs 1 and 2.

## The false positive

`free-order-skip-x-money-format` came out as a conflict. Its label is right:
change A drops the success event for any order under 100 minor units, which
is a bug in A alone, and change B is unrelated. By the rules in
`corpus/README.md`, the false positive counts against the generator.

The generator found A's bug twice. `test_paid_yen_events.py` passes on the
base and fails on A, so it is `regression_a`, which is the case's expected
finding. `test_formatted_yen_revenue.py` checks the same bug but reads the
result through B's new `format_amount`. That file can't import on the base or
on A, passes on B, and fails on the merge, so the four-way table reads it as
`differential_b`: B's behavior lost when A lands.

The table can't tell the two apart. A scenario that depends on one side's new
code can't run on the trees without it, so a bug in the other side alone
looks like a lost behavior. The same pattern carries real detections:
`receipt-x-event-rename` imports A's new `receipts` module, can't run on the
base or on B, and is a true conflict. A rule that scored the pattern as
inconclusive would remove this false positive and also those true
detections, so no such rule was applied.

## Why these numbers flatter the generator

- Claude wrote every case, and Claude generated the scenarios, so they might
  share blind spots.
- Each real-repository change B describes the contract it changes and the
  users it updated. In `cachetools-mru-x-fast-get`, the rationale repeats
  that sentence. Real pull requests don't always say this much.
- The three real-repository conflicts follow one shape, and none is emergent.
- Each pair got one generation. The toy cases are unchanged from run 2, and
  `free-order-skip-x-money-format` came out differently in runs 1, 2, and 3.
- Six conflict cases can't separate 61% recall from 100%, and six clean pairs
  can't show a false-positive rate under 56%. Showing under 5% needs at least
  73 clean pairs with none flagged.
