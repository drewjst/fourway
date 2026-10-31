# Run 1: Claude Opus 5.5 on corpus v1

**Date:** 2026-10-30 · **Generator:** `claude`, `claude-opus-5-5`, effort `high`,
one generation per pair · **Test repeats:** 3 · **Commit:** `aefbd0a`

| Measure | Result |
|---|---|
| Recall | 3/3 (95% CI 44% to 100%) |
| False positives | 1/3 (95% CI 6% to 79%) |
| Generator errors | 0/6 |
| Fallbacks | 0/6 |
| Cost | $0.51 total, $0.08 per pair (1,936 to 4,128 output tokens per pair) |

## Detections

Each detection names the seeded mechanism in its rationale:

- `retry-x-nonce-key`: the retry calls `idempotency_key()` again on every
  attempt, and B makes each call return a new key. Three emergent findings.
- `cache-x-set-price`: `set_price` writes the backend while the price is still
  cached. Three `differential_b` findings.
- `receipt-x-event-rename`: the receipt subscriber listens for an event that no
  longer fires. Two `differential_a` and two emergent findings.

## The false positive is a corpus labeling error

`cache-x-quote` is labeled clean, but the base already has a runtime write path,
`InMemoryPrices.write()`, and A's cache ignores it. A alone makes `price()`
stale. The generator wrote a test that `quote()` reflects a backend write, which
fails on the merge and is a valid `differential_b` finding by the table's
definition. The same flaw underlies part of `cache-x-set-price`.

After this run, the owner ruled to remove `write()` from the base tree. Corpus
v2 holds that fix, as described in [`corpus/README.md`](../../corpus/README.md).
The numbers on this page are v1 numbers and stay as recorded.

## Why these numbers flatter the generator

- Claude wrote the corpus, and Claude generated the scenarios, so they may
  share blind spots.
- The whole app fits in a prompt of about 5,000 tokens. Real repositories need
  file selection.
- Each pair got one generation, so variance between generations is unmeasured.
- Three conflict cases cannot separate 50% recall from 100%.
