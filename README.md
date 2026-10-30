# fourway

Two changes pass their own tests and merge without a conflict. Together, they
break. fourway looks for that.

For a pair of changes, fourway takes scenario tests aimed at how the two
changes interact and runs each scenario on four trees: the base, change A,
change B, and the merge of A and B. The pattern of the four outcomes says
whether the pair conflicts. A scenario that passes on A and on B and fails on
the merge is a reproduction that the author of either change can run.

## Example

Change A retries gateway timeouts in `charge()`. Change B gives every gateway
request a fresh idempotency key, so a customer can pay again after a decline.
Each change passes its own tests, and the two merge cleanly. Together, when
the gateway captures the funds and then times out, the retry sends a new key
and the customer is charged twice.

No existing test catches this, because nobody wrote the scenario. This pair is
the `retry-x-nonce-key` case in the benchmark corpus.

## How a scenario is classified

| base | A    | B    | A+B  | Finding          | Meaning                                         |
|------|------|------|------|------------------|-------------------------------------------------|
| any  | pass | pass | fail | `emergent`       | Each change holds; only the combination breaks. |
| fail | pass | fail | fail | `differential_a` | A's new behavior is lost when B lands.          |
| fail | fail | pass | fail | `differential_b` | B's new behavior is lost when A lands.          |
| pass | fail | pass | fail | `regression_a`   | A breaks it alone. This is an ordinary bug in A. |
| pass | pass | fail | fail | `regression_b`   | B breaks it alone. This is an ordinary bug in B. |
| fail | fail | fail | fail | `inconclusive`   | The scenario never passes, so it proves nothing. |
| any  | any  | any  | pass | `ok`             | The merge keeps the behavior.                   |

Only `emergent` and `differential_*` findings are conflicts. A skip on the
merge is never a failure, and a test whose outcome changes between repeated
runs is `flaky` and excluded. A pair with no usable scenario is `unverified`,
never `clean`.

## Status

This is Phase 0: a benchmark, not a tool to run on your pull requests yet.
Phase 0 answers one question: do generated scenarios find enough seeded
conflicts, with few enough false alarms, at a reasonable cost per pair?
Published test-generation approaches found about a third of semantic conflicts
(SAM detected 9 of 29). The bar for going further is at least 50% recall on
seeded conflicts, under 5% false positives on clean pairs, and under $5 per
pair.

The repository contains the following:

- The four-way runner, the classifier, and an evidence ledger keyed on the
  commits, environment, and scenario set that were verified.
- A seeded corpus: one small payments app and six pairs of changes with known
  answers. For details, see [`corpus/README.md`](corpus/README.md).
- Three control generators: `null`, `oracle`, and `deranged`.

It doesn't contain a model-backed scenario generator, cases seeded into real
repositories, or a sandboxed runner.

## Usage

Install with [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

Validate the corpus against its own answer key:

```bash
uv run fourway check-corpus
```

Score a generator:

```bash
uv run fourway bench --generator oracle
```

Run your own scenario tests four ways on two branches of a repository:

```bash
uv run fourway pair --repo PATH --base main --a branch-a --b branch-b --scenarios DIR
```

## Why the controls exist

A benchmark score is not evidence until it can come out wrong. The controls
show that the score responds to the scenarios and not to the corpus:

- `null` writes no scenarios. Every pair must come out `unverified`.
- `oracle` uses each case's hidden answer scenario. It must find every seeded
  conflict and flag no clean pair.
- `deranged` gives each case the answer scenario of a different case. Its
  recall must fall well below the oracle's.

The test suite enforces all three.

## Security

A generated scenario is code that a model wrote from diff text. If the diff
comes from someone you don't trust, a prompt injection in the diff can steer
the model into writing a test that runs anything. Until the runner executes
scenarios in a container with no network and no credentials, run fourway only
on changes you wrote. For details, see
[decision 0002](docs/decisions/0002-generated-scenarios-run-only-on-trusted-diffs.md).

## Research

- Da Silva et al., *Detecting Semantic Conflicts with Unit Tests* (SAM),
  Journal of Systems and Software, 2024.
- Barbosa, Borba, and Da Silva, *Assessing the Effectiveness of LLMs in
  Detecting Semantic Conflicts*, 2026.

## License

Apache-2.0. See [LICENSE](LICENSE).
