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

For a plain-language overview, see the project page at
[drewjst.github.io/fourway](https://drewjst.github.io/fourway/). Its source is
[`site/`](site/), and `.github/workflows/pages.yml` deploys it when `site/`
changes on `main`.

The repository contains the following:

- The four-way runner, the classifier, and an evidence ledger keyed on the
  commits, environment, and scenario set that were verified.
- A seeded corpus of twelve pairs of changes with known answers: six in a
  small payments app and six in real repositories. For details, see
  [`corpus/README.md`](corpus/README.md).
- Clean pairs mined from real pull requests: two pull requests that were open
  at the same time and landed back to back. The mining rule is fixed in
  `fourway mine` and stated in the corpus README.
- Three control generators: `null`, `oracle`, and `deranged`.
- A Claude-backed generator, `claude`, that writes intent and invariant
  scenarios from the base tree, both diffs, and both change descriptions. Each
  scored run is recorded in [`results/`](results/).

The corpus also has six cases seeded into pinned commits of three real
repositories: `cachetools`, `tenacity`, and `tinydb`. Checking the corpus runs
those repositories' test suites, locally unless you pass `--sandbox`.

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

Model-written scenarios run on mined pairs only in the sandbox, a container
with no network, no credentials, and a read-only tree. `bench` refuses them
without `--sandbox`; `--seeded-only` leaves the mined pairs out instead. The
controls run anywhere. Build the sandbox image once, with Docker running:

```bash
uv run fourway sandbox build
```

Mine clean pairs from a pinned repository's history, then check them. The
corpus README lists the commands that fetch the inputs:

```bash
uv run fourway mine NAME --clone NAME.git --prs NAME.prs.jsonl --cutoff 2026-10-31
```

```bash
uv run fourway check-corpus --prune-mined
```

Score the Claude generator. This calls the Claude API once per case and needs
`ANTHROPIC_API_KEY` in the environment. The `--out` directory keeps every
generated scenario and its four outcomes:

```bash
uv run fourway bench --generator claude --sandbox --repeat 3 --out runs/claude
```

Rescore the scenarios that an earlier run saved, without calling the API. A
change to the runner or the classifier then shows its effect on the same
generated files:

```bash
uv run fourway bench --generator replay --from results/2026-10-30-claude-opus-5-5-run2 --repeat 3
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
the model into writing a test that runs anything. Run scenarios on changes
you didn't write only with `--sandbox`: each tree's tests then run in a
container with no network, no credentials, and a read-only copy of the tree.
`fourway pair` uses the sandbox unless you pass `--trusted`. The sandbox
contains a scenario but doesn't make its verdict trustworthy, and containers
share the host's kernel on Linux. For details, see
[decision 0002](docs/decisions/0002-generated-scenarios-run-only-on-trusted-diffs.md)
and [decision 0003](docs/decisions/0003-scenarios-on-third-party-changes-run-in-a-container.md).

## Research

- Da Silva et al., *Detecting Semantic Conflicts with Unit Tests* (SAM),
  Journal of Systems and Software, 2024.
- Barbosa, Borba, and Da Silva, *Assessing the Effectiveness of LLMs in
  Detecting Semantic Conflicts*, 2026.

## License

Apache-2.0. See [LICENSE](LICENSE).
