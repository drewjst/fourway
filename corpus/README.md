# Benchmark corpus

Each case is a pair of changes, A and B, to a base tree, with a known answer:
`conflict` or `clean`. A generator is scored on whether its scenarios produce
a `conflict` verdict on the conflict cases and not on the clean ones.

## Layout

```
apps/payments/            base tree shared by every case
cases/<id>/case.toml      label, expected oracle finding, class, and each side's description
cases/<id>/a/             files change A adds or replaces
cases/<id>/b/             files change B adds or replaces
cases/<id>/oracle/        the hidden scenario that demonstrates the answer
```

## Cases

The following table lists the cases. A clean twin makes the same change A as a
conflict case and a different change B, so a generator can't score by matching
on the files a pair touches. Two of the three conflict cases have a twin, and
`tests/test_bench.py` checks that twins share change A. The twin for
`receipt-x-event-rename` is tracked in issue #5.

| Case | Label | Oracle finding | What happens on the merge |
|---|---|---|---|
| `retry-x-nonce-key` | conflict | `emergent` | A retry after a lost response sends a fresh key and charges twice. |
| `retry-x-currency-key` | clean | `ok` | Keys still repeat per order, so the retry is deduplicated. |
| `cache-x-set-price` | conflict | `differential_b` | A price change never reaches a catalog that already cached the price. |
| `cache-x-quote` | clean | `ok` | Quotes read through the cache and stay correct. |
| `receipt-x-event-rename` | conflict | `differential_a` | The receipt handler listens for an event name that no longer fires. |
| `free-order-skip-x-money-format` | clean | `regression_a` | A breaks small paid orders by itself. B is unrelated. |

## Rules for a case

`fourway check-corpus` enforces the first three rules:

1. A and B merge without a textual conflict.
2. The existing test suite passes on base, A, B, and the merge, so ordinary CI
   on the merge cannot see the problem.
3. The oracle produces the expected finding, and its verdict matches the
   label.
4. Each description says what its change does and why, as its author would.
   It never mentions the other change or the interaction.
5. Nothing a generator can see names the case, the label, or the oracle.
   `tests/test_bench.py` checks this for the oracle source and the case id.

## Adjudicate a false positive

A false positive is read before it counts. It counts against the generator
unless the scenario shows that the label is wrong. A wrong label is fixed in a
new corpus version and measured by a new run. The following rules were set
before run 2:

- Descriptions are true statements about the code. A scenario that contradicts
  one counts against the generator. For example, in `cache-x-quote`, change A
  says that prices change only when the price list is redeployed, so a test
  backend whose prices change while the app runs contradicts it.
- A scenario that reaches a state through a private attribute, for example by
  assigning to `InMemoryPrices._prices`, tests a state that the app can't
  enter. It counts against the generator.

## Versions

Runs on different corpus versions are reported separately and never pooled.

- **v2, 2026-10-30**: The base `InMemoryPrices` has no `write()`, so the base
  app can't change a price while it runs. In `cache-x-set-price`, change B adds
  `write()` along with `set_price`, and its description no longer says that the
  admin editor wrote to the backend directly. Change A in both cache cases says
  that prices change only when the price list is redeployed. Run 1 showed that
  in v1, change A's cache went stale by itself, so `cache-x-quote` held a real
  `differential_b` and wasn't clean.
- **v1, 2026-10-30**: The first six cases. Run 1 used this version.

## Known limits

The cases were written by the same person who builds the generators, in a
purpose-built app with a fake gateway that already supports fault schedules.
Recall here is an upper bound on recall in a real repository. Cases seeded
into real open-source repositories are tracked as a GitHub issue.
