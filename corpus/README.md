# Benchmark corpus

Each case is a pair of changes, A and B, to a base tree, with a known answer:
`conflict` or `clean`. A generator is scored on whether its scenarios produce
a `conflict` verdict on the conflict cases and not on the clean ones.

## Layout

```
apps/payments/            base tree shared by the toy cases
repos/<name>.toml         a real repository pinned to one commit
cases/<id>/case.toml      label, expected oracle finding, class, and each side's description
cases/<id>/a/, b/         files change A or B adds or replaces
cases/<id>/a.patch, b.patch  a diff change A or B applies, for cases in a real repository
cases/<id>/oracle/        the hidden scenario that demonstrates the answer
cases/<repo>-<A>-x-<B>/   a clean pair mined from pull requests A and B; case.toml only
```

A case's `base` is either a path to a directory, such as
`"../../apps/payments"`, or a table that names a pinned repository, such as
`{ repo = "cachetools" }`.

## Real repositories

A file in `repos/` pins one commit of a real repository and says how its
tests run:

```toml
url = "https://github.com/OWNER/NAME"
commit = "FULL_40_CHARACTER_SHA"
license = "MIT"
tests = "tests"                  # the repository's own suite
pythonpath = ["src"]             # added to sys.path after the repository root
pytest_args = ["-o", "addopts="] # added to every pytest run in the repository
packages = ["src/NAME/"]         # where the package's code lives, for fourway mine
```

`commit` is the default base for the repository's seeded cases. A case's
`base` table can name its own `commit`, and can override `tests`,
`pythonpath`, or `pytest_args` when the layout at that commit differs.

fourway fetches the commit once into `~/.cache/fourway`, or into
`$FOURWAY_CACHE` when it is set, and builds every case from that copy. It
refuses a short SHA, a commit the URL doesn't provide, and a repository whose
`.gitattributes` uses `export-ignore` or `export-subst`.

Cases in a real repository change it with patches, not whole files, so the
corpus carries only the seeded lines of upstream code. An upstream test that
is skipped, for example because an optional dependency is absent, doesn't
count as red.

Building these cases runs the upstream repository's code: its test suite on
four trees, and every scenario against its modules. Pin only commits of
projects you would install.

## Mined pairs

A mined pair comes from a pinned repository's history instead of being
seeded. It uses the same case format, with three differences:

- Each side names two upstream commits, `from` and `to`, and the change is
  the diff between them. The corpus carries no upstream code, only commit
  SHAs and each pull request's title, link, and description.
- The `base` table names the base commit.
- It has no `oracle/` and no `expect`. Its label is always `clean`, and the
  label rests on history: the project merged both changes and reverted
  neither. That is an assumption, not a verified fact. A latent conflict that
  nobody noticed still carries the clean label.

### The mining rule

`fourway mine` applies the rule, and `src/fourway/mine.py` defines it. The rule
was fixed on 2026-10-31, before any generator ran on a mined pair:

1. Take the pull requests merged before the cutoff whose author isn't a bot.
   A bot has the GitHub user type `Bot`, or a login that ends in `[bot]` or
   `-bot`.
2. Keep the ones that landed on the default branch as one first-parent
   commit: a merge commit, or a squash commit whose subject ends in `(#N)`. A
   rebase merge spreads a pull request over commits that the history can't
   delimit, so it is skipped.
3. A landing is code if it changes a Python file in the package, outside test
   directories and `test_*` files.
4. Walk the code landings in order. Pair each one with the next if that pull
   request was opened before the first one merged. A pull request joins at
   most one pair, so the pairs count as independent trials.
5. Drop a pair if any commit reverts either side, by SHA or by subject.
6. Drop a pair if the generator can't see its base tree: the files that
   `TREE_RULE` shows exceed 400,000 characters.
7. `fourway check-corpus --prune-mined` drops a pair that doesn't build,
   conflicts textually, or has an existing suite that isn't green on all four
   trees. Change B must apply to the base by itself, so a B written on top of
   A drops out here.

The base is the default branch just before A landed, so tree A is the one the
project shipped. The merge equals the tree the project shipped after B only
when nothing else landed between them. Tree B alone never existed.

A mined pair's diffs and descriptions come from people outside this project,
so [decision 0002](../docs/decisions/0002-generated-scenarios-run-only-on-trusted-diffs.md)
applies: a generator's scenarios run on mined pairs only in the sandboxed
runner (issue #2). `check-corpus` runs only the upstream suites, not
generated code.

Mining reads history and never runs upstream code; `check-corpus` runs it. To
mine a repository, run these commands. The first two write the inputs
outside the corpus:

```bash
gh api 'repos/OWNER/NAME/pulls?state=closed&per_page=100' --paginate --jq '.[] | select(.merged_at) | {number, html_url, title, body, user: .user.login, user_type: .user.type, created_at, merged_at, merge_commit_sha}' > NAME.prs.jsonl
```

```bash
git clone --bare --filter=blob:none https://github.com/OWNER/NAME NAME.git
```

```bash
uv run fourway mine NAME --clone NAME.git --prs NAME.prs.jsonl --cutoff 2026-10-31
```

```bash
uv run fourway check-corpus --prune-mined
```

### Score and adjudicate mined pairs

These rules were set on 2026-10-31, before any generator ran on a mined
pair:

- A false-positive rate counts only the clean pairs that the generator
  verified. An unverified pair is reported beside the rate and left out of
  it, because it shows nothing either way; counting it as a pass gave the
  `null` control, which writes no scenarios, a rate of 0/30. No earlier run
  had an unverified clean pair, so no recorded rate changes.
- A report gives the false-positive rate on all clean pairs, and beside it
  the rate on each of these groups, which `bench` prints:
  - Seeded twins.
  - `mined, same file` and `mined, other files` pairs. Changes that touch
    different files are easier to call clean.
  - Mined pairs where both sides change runtime code. `fourway mine` records
    in `runtime` the sides whose package code changes beyond docstrings,
    annotations, comments, and layout, by comparing syntax trees. A side that
    changes none of it can hardly conflict.
  - Mined pairs where no side credits an AI assistant. `fourway mine` records
    in `assisted` the sides whose description or landing commit credits one,
    for example in a `Co-Authored-By` trailer. Uncredited help goes uncounted,
    so this group is an upper bound on pairs that no model wrote.
- A flagged mined pair counts as a false positive, under the rules in
  [Adjudicate a false positive](#adjudicate-a-false-positive), unless the
  scenario shows a defect on the merge that the package's public API reaches.
  When the merge equals the commit the project shipped, the scenario must
  fail on that commit too. A pair that meets both conditions is a conflict
  the history missed. It is reported as a finding, and the owner decides
  whether a new corpus version relabels it.
- Before the first run on mined pairs, the corpus author reads a random
  sample of them and judges whether either change alters behavior that the
  other relies on. The
  sample and the judgments are recorded in
  [Hand check of mined labels](#hand-check-of-mined-labels). A wrong label in
  the sample means the rule is wrong; the rule changes, not the label.

### Hand check of mined labels

On 2026-10-31, before any generator ran on a mined pair, the corpus author
read 10 of the 24 mined pairs. The sample was drawn with
`random.Random(20261031).sample` over the sorted case ids. Every label holds:
neither change alters behavior that the other relies on.

| Pair | Change A | Change B |
|---|---|---|
| `tenacity-424-x-423` | Compares the Python version as a tuple, for pyright | Adds `stop_before_delay` |
| `tenacity-435-x-434` | Reformats the package with ruff | Builds `iter()` from a list of actions |
| `tenacity-484-x-425` | Sets a wrapped function's `retry` attribute back to the retrying object | Makes `wait_random_exponential` respect `min` |
| `tenacity-586-x-587` | Drops a positional-only marker from `LoggerProtocol.log` | Removes an unused `IterState` field |
| `tenacity-588-x-589` | Removes a dead `raise` before `reraise()` | Annotates with `re.Pattern` instead of `typing.Pattern` |
| `tenacity-606-x-605` | Lets `\|` and `&` combine a retry strategy with a plain callable | Adds `async with` to `AttemptManager` |
| `tenacity-654-x-651` | Returns the cap before computing a large power in `wait_exponential` | Accepts an empty message in `retry_if_exception_message` |
| `tinydb-188-x-184` | Changes a format string in a `repr` | Adds `Table.write_back()` |
| `tinydb-337-x-340` | Fixes a docstring example | Uses `move_to_end()` in `LRUCache` |
| `tinydb-640-x-642` | Adds regex flags to query hashes | Stops `persist_empty` from clearing an existing table |

The sample showed three things:

- Six of the ten pairs have a side that changes little or no runtime
  behavior: types, formatting, a docstring, or a dead statement. Such pairs
  are easy to call clean, so reports break out the pairs where both sides
  change runtime code.
- Change B of `tinydb-337-x-340` has a bug of its own: `LRUCache.set` stops
  updating the value of an existing key, which tinydb fixed in 2024. The label
  still holds, because change A only fixes a docstring. A scenario that
  catches the bug scores `regression_b`, which isn't a conflict.
- Both sides of 8 of the 24 mined pairs credit Claude Opus 4.6 in a
  `Co-Authored-By` trailer. Mined pairs reduce the shared-author problem but
  don't remove it.

## Cases

The following table lists the cases. A clean twin makes the same change A as a
conflict case and a different change B, so a generator can't score by matching
on the files a pair touches. Five of the six conflict cases have a twin, and
`tests/test_bench.py` checks that twins share change A. The twin for
`receipt-x-event-rename` is tracked in issue #5.

The first six cases share the toy payments app in `apps/payments/`. The other
six seed changes into pinned commits of three real repositories, listed in
`repos/`. The mined pairs aren't listed here; each one's `case.toml` links its
two pull requests.

| Case | Label | Oracle finding | What happens on the merge |
|---|---|---|---|
| `retry-x-nonce-key` | conflict | `emergent` | A retry after a lost response sends a fresh key and charges twice. |
| `retry-x-currency-key` | clean | `ok` | Keys still repeat per order, so the retry is deduplicated. |
| `cache-x-set-price` | conflict | `differential_b` | A price change never reaches a catalog that already cached the price. |
| `cache-x-quote` | clean | `ok` | Quotes read through the cache and stay correct. |
| `receipt-x-event-rename` | conflict | `differential_a` | The receipt handler listens for an event name that no longer fires. |
| `free-order-skip-x-money-format` | clean | `regression_a` | A breaks small paid orders by itself. B is unrelated. |
| `cachetools-mru-x-fast-get` | conflict | `differential_a` | A's new `MRUCache` stops counting `get()` as a use, because B's fast `get()` skips `__getitem__` for every class it didn't update. |
| `cachetools-mru-x-peek` | clean | `ok` | `peek()` doesn't count as a use by design, and `get()` still does. |
| `tenacity-idle-budget-x-stop-first` | conflict | `differential_a` | A's `stop_before_idle` reads a stale `upcoming_sleep`, because B runs the stop strategy before the wait. The sleep budget is overspent. |
| `tenacity-idle-budget-x-sleep-override` | clean | `ok` | B changes only the accounting after `before_sleep`, so the budget check is unchanged. |
| `tinydb-warm-cache-x-ordered-search` | conflict | `differential_b` | A appends an inserted document to cached results, so a cached search loses B's document ID order. |
| `tinydb-warm-cache-x-cached-count` | clean | `ok` | `count()` reads the cached result that A keeps up to date. |

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

- **v4, 2026-10-31**: Adds 24 clean pairs mined from the pull request
  history of `tenacity` (15) and `tinydb` (9). Of 48 candidates, 24 dropped
  out in `check-corpus`: 7 changes B didn't apply to the base by themselves,
  and 17 suites were red on the base under Python 3.12 or typeguard 4. In
  `repos/tenacity.toml`, `pytest_args` ignores `test_tornado.py` with a glob,
  which ignores the same file at the v3 commit. fourway's dev environment
  adds typeguard. The seeded cases are unchanged from v3.
- **v3, 2026-10-30**: Six cases in three real repositories: `cachetools`,
  `tenacity`, and `tinydb`. Each is a conflict and its clean twin. The toy
  cases are unchanged from v2.
- **v2, 2026-10-30**: The base `InMemoryPrices` has no `write()`, so the base
  app can't change a price while it runs. In `cache-x-set-price`, change B adds
  `write()` along with `set_price`, and its description no longer says that the
  admin editor wrote to the backend directly. Change A in both cache cases says
  that prices change only when the price list is redeployed. Run 1 showed that
  in v1, change A's cache went stale by itself, so `cache-x-quote` held a real
  `differential_b` and wasn't clean.
- **v1, 2026-10-30**: The first six cases. Run 1 used this version.

## Known limits

The same author wrote every case and the generators. The toy cases live in a
purpose-built app with a fake gateway that already supports fault schedules.
The real-repository cases fix the toy app's size and idioms, but not the
shared author.

The three real-repository conflicts follow one pattern: one change adds a new
user of an unwritten contract, and the other change alters the contract and
updates every user that existed when it was written. All three are
differential findings. None is emergent, and each twin's change B touches the
same file as the conflict's change B. Recall on these cases is still an upper
bound on recall against conflicts nobody seeded.

Mined pairs fix the shared author for clean pairs, but they have limits of
their own. History vouches for a clean label only as far as nobody noticed a
problem. Tree B alone is a tree nobody shipped. The rule drops pairs whose
suites need a dependency fourway doesn't install, pairs whose base trees
exceed the generator's budget, and pairs from Python versions older than the
one fourway runs on, so the mined pairs lean toward recent, small
repositories.
