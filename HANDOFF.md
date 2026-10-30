# HANDOFF — fourway
State:    building — Claude generator written and tested offline; not yet run against the API
Next:     with ANTHROPIC_API_KEY set, run `uv run fourway bench --generator claude --repeat 3 --out runs/claude`, read every miss in runs/claude/, and record recall, false positives, and cost per pair on issue #1
Blockers: no Anthropic credentials on this machine (`ANTHROPIC_API_KEY` unset, `ant` not installed); the first paid run needs the owner's go-ahead
Decisions this session:
- Phase 0 is a benchmark only — no recall number exists to put behind an integration — rejected: GitHub App first (docs/decisions/0001)
- Scenarios run as local subprocesses only on the seeded corpus — generated code from attacker-controlled diffs is a prompt-injection path to code execution — rejected: declarative scenarios, filtered-env local runner (docs/decisions/0002)
- Every conflict case has a clean twin that changes only side B — stops a generator from scoring by matching on touched files — rejected: unrelated clean controls
- A pair with no usable scenario is `unverified`, never `clean` — an agent asking "was this verified?" must not hear yes when nothing ran — rejected: empty result reads as clean
- Corpus check allows a test that is missing from a tree — a side may delete a test; only a red test would alert CI — rejected: requiring every test to exist on the merge
- Corpus files are copied with fresh mtimes — copy2 kept source mtimes, so on a fresh CI checkout git's stat cache skipped same-size overlay files and a seeded conflict read as clean (caught by check-corpus on CI; tests/test_case.py) — rejected: forcing `git add --renormalize` on every commit (re-hashes every tracked file in real repos)
- Recall and false positives are reported as k/n with Wilson 95% intervals — six cases cannot support a percentage — rejected: bare percentages
- Generator calls Claude through the Anthropic API key, not headless Claude Code — exact token counts per call, and cost per pair is a Phase 0 gate — rejected: `claude -p` (system-prompt overhead pollutes cost)
- Generator defaults: claude-opus-5-5, effort high, adaptive thinking, JSON-schema output, one sample per pair — rejected: tool-call output (forced tool_choice 400s on Opus 5.5), multi-sample ensembles (measure one model first)
- Refusal fallbacks are on (`fallbacks: "default"`), and any fallback is flagged in the report and the evidence record — a fallback changes whose recall the number is — rejected: no fallbacks (a refusal would silently read as a miss)
- Python stays for Phase 0; Go is the recommended language for the sandboxed runner (#2) — language does not change recall, and container orchestration and single-binary install are where Go pays off — rejected: porting before the recall number exists. Recommendation only; the owner has not ruled
Pointers: main · github.com/drewjst/fourway (public) · issues #1–#4 hold deferred work · `uv run pytest -q` (48 tests, about 35 s, no network) · src/fourway/claude.py · `fourway bench --generator claude|oracle|null|deranged` · corpus/README.md · docs/decisions/
