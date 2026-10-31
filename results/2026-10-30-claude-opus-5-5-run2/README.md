# Run 2: Claude Opus 5.5 on corpus v2

**Date:** 2026-10-30 · **Generator:** `claude`, `claude-opus-5-5`, effort `high`,
one generation per pair · **Test repeats:** 3 · **Commit:** `c564309`

Run 2 has two scores. The first is the run as recorded. The second replays the
same generated files with the runner fixed in `3b1893c`, without calling the
API. The fix is for a fourway bug that run 2 exposed.

| Measure | As recorded | Rescored at `3b1893c` |
|---|---|---|
| Recall | 3/3 (95% CI 44% to 100%) | 3/3 (95% CI 44% to 100%) |
| False positives | 1/3 (95% CI 6% to 79%) | 0/3 (95% CI 0% to 56%) |
| Generator errors | 0/6 | 0/6 |
| Fallbacks | 0/6 | 0/6 |
| Cost | $0.47 total, $0.08 per pair (2,131 to 4,330 output tokens per pair) | No new calls |

`report.txt` and the case folders hold the run as recorded. `rescored/` holds
the replay's report and outcomes. To reproduce the rescore, run the following
command:

```bash
uv run fourway bench --generator replay --from results/2026-10-30-claude-opus-5-5-run2 --repeat 3
```

## The false positive was a fourway bug

`free-order-skip-x-money-format` came out as a conflict. One scenario file,
`test_receipt_formatting.py`, imports `payments.money`, which only change B
adds. On the base and A trees, that import failed, and pytest stops the whole
session on a collection error by default. Every other scenario on those trees
was reported as `missing`, and the classifier read `missing` on base as a
failure. A test that passes on base, fails on A, passes on B, and fails on the
merge is `regression_a`. With base unknown, it read as `differential_b`.

The generator's test was right. Its rationale says that A's 100-unit threshold
drops the success event for a 50-yen charge, which is a real paid charge. That
is the regression the case seeds in A, and `regression_a` is the case's
expected finding.

The fix passes `--continue-on-collection-errors` to pytest. A synthetic pair in
`tests/test_pipeline.py` reproduces the old misreading and fails without the
fix.

## What the rescore changed

The rescore changed six outcomes, and every one of them was `missing` before:

- `free-order-skip-x-money-format`: two tests went from `differential_b` to
  `regression_a`, and two `ok` tests got real outcomes on base and A. The
  verdict went from `conflict` to `regression`.
- `receipt-x-event-rename`: two `ok` tests got real outcomes on base and B.
  The verdict stayed `conflict`.

No conflict finding in run 2 depended on a `missing` outcome, so the bug didn't
raise recall. Run 1 has no `missing` outcomes, so the bug didn't affect run 1.

## Detections

Each detection names the seeded mechanism in its rationale:

- `retry-x-nonce-key`: the retry builds the idempotency key inside the loop,
  and B makes every call return a new key, so a lost response is captured
  twice. Three emergent and two `differential_a` findings.
- `cache-x-set-price`: a price read before `set_price` is still served from
  A's cache, so the admin's change is invisible. Two `differential_b`
  findings.
- `receipt-x-event-rename`: A's receipt subscriber listens on the old event
  name, so a real `charge()` writes no receipt after the merge. Three
  `differential_a` findings.

`cache-x-quote`, the pair corpus v2 fixed, came out clean with six `ok`
findings. None of the six scenarios changes a price.

## Comparison with run 1

Run 1 used corpus v1, so the two runs aren't pooled. On the four cases that
didn't change between versions, each run wrote different scenarios. In
`free-order-skip-x-money-format`, run 1 wrote six `ok` tests and missed A's
regression, and run 2 found it. One generation per pair hides that variance in
each run's score.

## Why these numbers flatter the generator

- Claude wrote the corpus, and Claude generated the scenarios, so they might
  share blind spots.
- The whole app fits in a prompt of about 5,000 tokens. Real repositories need
  file selection.
- Each pair got one generation, and the two runs show that the scenarios vary
  from one generation to the next.
- Three conflict cases can't separate 50% recall from 100%.
- The rescored false-positive rate comes from a fix made after the score was
  seen. The fix is general and has a synthetic test, and it changed only
  outcomes that were `missing`, but the as-recorded number stays the one of
  record.
