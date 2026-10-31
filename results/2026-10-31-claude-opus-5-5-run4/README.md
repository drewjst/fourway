# Run 4: Claude Opus 5.5 on corpus v5, in the sandbox

**Date:** 2026-10-31 · **Generator:** `claude`, `claude-opus-5-5`, effort `high`,
one generation per pair · **Test repeats:** 3 · **Sandbox:**
`fourway-sandbox:ecf384df0549` · **Commit:** `c665fc9`

Corpus v5 adds 76 clean pairs mined from the pull request history of six
real repositories to the 12 seeded cases of v3. Every tree's tests ran in the
sandbox that decision 0003 describes. Each flagged clean pair was adjudicated
under the rules that `corpus/README.md` set before this run.

| Measure | As recorded | After adjudication |
|---|---|---|
| Recall | 6/6 (95% CI 61% to 100%) | 6/6 (95% CI 61% to 100%) |
| False positives | 3/82 (95% CI 1% to 10%) | 2/81 (95% CI 1% to 9%) |
| Unverified pairs | 0/88 | 0/88 |
| Generator errors and fallbacks | 0/88 | 0/88 |
| Cost | $36.97 in all, $0.42 per pair | |

The most expensive pair, `tomlkit-668-x-658`, cost $1.35 for 330,000 input
tokens, because its change A adds a 1,661-line `uv.lock`. The run took 63
minutes and used 7.38 million input tokens and 0.37 million output tokens.

The false-positive groups that `bench` printed, as recorded:

| Group | False positives |
|---|---|
| Seeded twins | 1/6 (95% CI 3% to 56%) |
| Mined, same file | 2/30 (95% CI 2% to 21%) |
| Mined, other files | 0/46 (95% CI 0% to 8%) |
| Mined, both sides change code | 2/54 (95% CI 1% to 13%) |
| Mined, no side AI-credited | 1/64 (95% CI 0% to 8%) |

## Against the Phase 0 bar

- **Recall at least 50%:** the lower bound is 61%, on six seeded conflicts
  that Claude wrote.
- **False positives under 5%:** not shown. The point estimate is 2.5%, but the
  upper bound is 9%. With two false positives, the upper bound falls under 5%
  at 142 verified clean pairs, if no new false positive appears.
- **Under $5 per pair:** $0.42 on average, and $1.35 at most.

## The flagged clean pairs

### `free-order-skip-x-money-format`: false positive

This is the same flag as in run 3. Change A drops the success event for small
orders, a bug in A alone. A scenario reads it through change B's new
`format_amount`, so it can't run on the base or on A, and the four-way table
reads it as `differential_b`. The label is right, so the flag counts.

### `tenacity-351-x-342`: a conflict the history missed

Change A ([jd/tenacity#351](https://github.com/jd/tenacity/pull/351)) adds the
wait strategy `wait_exponential_jitter`. Change B
([jd/tenacity#342](https://github.com/jd/tenacity/pull/342)) makes every wait
strategy accept a `datetime.timedelta` and converts each one that existed when
it was written. #342 was open from January 2022, and the two merged about a
month apart, on 2022-04-27 and 2022-05-30. On the
merge, every wait strategy with a `max` parameter accepts a `timedelta` except
`wait_exponential_jitter`, which fails when it's called. The generated
scenario checks every strategy and scores `differential_b`.

The evidence meets the conditions set before the run:

- The defect is on the merge, and the public API reaches it:
  `tenacity.wait_exponential_jitter(max=timedelta(seconds=5))`.
- The merge doesn't equal a shipped commit, because another commit landed
  between the two. The scenario also fails on the commit the project shipped
  after both, `18d05a6`. A direct probe in the sandbox there finds every other
  strategy accepting a `timedelta` maximum.
- Neither side alone has the defect. On A alone, no strategy accepts a
  `timedelta`, and on B alone, `wait_exponential_jitter` doesn't exist.

The project added `timedelta` support to `wait_exponential_jitter` on
2026-03-11, in [jd/tenacity#628](https://github.com/jd/tenacity/pull/628), more
than three years later. This is the conflict shape the corpus seeds by hand:
one change adds a new user of a convention, and the other changes the
convention and updates every user it knew about. The pair isn't counted as a
false positive. The owner decides whether a new corpus version relabels it.

### `tomlkit-565-x-567`: false positive

Change A ([python-poetry/tomlkit#565](https://github.com/python-poetry/tomlkit/pull/565))
lets the parser accept an out-of-order super-table extended by a dotted key.
Change B ([python-poetry/tomlkit#567](https://github.com/python-poetry/tomlkit/pull/567))
renders an emptied array of tables as an empty array. The scenario parses a
document only A accepts, empties the array of tables, and finds that the
output no longer parses. It passes on A and fails on the merge, which equals
the commit the project shipped, so it scores `differential_a`.

Probes on all four trees show that the defect is B's own. A document that the
base and B can both parse, `[[a.b.c]]` followed by `[a]`, round-trips on the
base and stops round-tripping on B alone, a `regression_b`. The scenario
reached B's bug through input that only A's parser accepts, which is the same
pattern as `free-order-skip-x-money-format` with the sides reversed.

The rule for mined pairs asks only for "a defect on the merge that the
package's public API reaches", which this flag meets. The flag is counted
anyway, because the defect doesn't come from the interaction, and that reading
is the one that doesn't flatter the generator. The rule's wording should say
so before the next run; this run is scored as described here.

The bug is still in `tomlkit` at `d7def7d` (2026-10-29): `parse` accepts
`[[a.b.c]]\nx = 1\n[a]\ny = 1\n`, and after the array's only entry is
removed, `as_string()` returns text that `parse` rejects with `ParseError`.

## Why these numbers flatter the generator

- Recall still rests on six seeded conflicts, all written by Claude, and all
  three real-repository conflicts follow one shape. The mined pairs measure
  false positives only.
- The adjudication was done by Claude, the generator's model family. The two
  judgments that change the score, `tenacity-351-x-342` and
  `tomlkit-565-x-567`, need the owner's review.
- Each pair got one generation, and `free-order-skip-x-money-format` has come
  out differently across runs.
- 29 of the 76 mined pairs have a side that changes no runtime code, or credit
  an AI assistant. The one mined false positive, `tomlkit-565-x-567`, credits
  one; after adjudication, the 63 mined pairs that credit none have no false
  positive.
- A clean label on a mined pair is an assumption about history, and this run
  found one that's wrong.
