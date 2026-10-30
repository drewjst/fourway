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

The following table lists the cases. Each conflict case has a clean twin that
makes the same change A and a different change B:

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

## Known limits

The cases were written by the same person who builds the generators, in a
purpose-built app with a fake gateway that already supports fault schedules.
Recall here is an upper bound on recall in a real repository. Cases seeded
into real open-source repositories are tracked as a GitHub issue.
