# HANDOFF — fourway
State:    building — Phase 0 harness done; no model-backed generator yet
Next:     write the first model-backed scenario generator (`src/fourway/generators.py`, blind `Generator` protocol) and score it with `fourway bench`
Blockers: model access for the generator: `ANTHROPIC_API_KEY` is not set on this machine
Decisions this session:
- Phase 0 is a benchmark only — no recall number exists to put behind an integration — rejected: GitHub App first (docs/decisions/0001)
- Scenarios run as local subprocesses only on the seeded corpus — generated code from attacker-controlled diffs is a prompt-injection path to code execution — rejected: declarative scenarios, filtered-env local runner (docs/decisions/0002)
- Every conflict case has a clean twin that changes only side B — stops a generator from scoring by matching on touched files — rejected: unrelated clean controls
- A pair with no usable scenario is `unverified`, never `clean` — an agent asking "was this verified?" must not hear yes when nothing ran — rejected: empty result reads as clean
- Corpus check allows a test that is missing from a tree — a side may delete a test; only a red test would alert CI — rejected: requiring every test to exist on the merge
- Recall and false positives are reported as k/n with Wilson 95% intervals — six cases cannot support a percentage — rejected: bare percentages
Pointers: main · `uv run pytest -q` (38 tests, about 30 s) · `uv run fourway bench --generator oracle|null|deranged` · corpus/README.md · docs/decisions/
