"""The Claude generator, tested offline against a fake client that records each request."""

import json
import math
from pathlib import Path
from types import SimpleNamespace

import pytest

from fourway import bench, claude, generators
from fourway.case import Intent, load_corpus
from fourway.generators import PairContext

CORPUS = Path(__file__).parents[1] / "corpus"
LOST_RESPONSE = (CORPUS / "cases/retry-x-nonce-key/oracle/test_lost_response.py").read_text()


def message(payload=None, *, stop_reason="end_turn", model="claude-opus-5-5",
            input_tokens=10_000, output_tokens=5_000, iterations=None):
    content = [SimpleNamespace(type="thinking", thinking="")]
    if payload is not None:
        content.append(SimpleNamespace(type="text", text=json.dumps(payload)))
    usage = SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens,
                            cache_creation_input_tokens=0, cache_read_input_tokens=0,
                            iterations=iterations)
    return SimpleNamespace(model=model, stop_reason=stop_reason, content=content, usage=usage)


class FakeClient:
    def __init__(self, reply):
        self.reply = reply
        self.requests = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(stream=self._stream))

    def _stream(self, **request):
        self.requests.append(request)
        reply = self.reply

        class Stream:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def get_final_message(self):
                return reply

        return Stream()


def scenario(filename, source=LOST_RESPONSE, kind="invariant"):
    return {"filename": filename, "kind": kind, "rationale": "r", "source": source}


@pytest.fixture
def ctx(tmp_path):
    (tmp_path / "app.py").write_text("X = 1\n")
    return PairContext(tmp_path, "diff-a-text", "diff-b-text", Intent("A title", "A body"),
                       Intent("B title", "B body"))


def test_the_request_asks_for_schema_valid_json_and_opts_into_fallbacks(ctx):
    client = FakeClient(message({"scenarios": []}))
    claude.ClaudeGenerator(client=client).generate(ctx)
    [request] = client.requests
    assert request["model"] == "claude-opus-5-5"
    assert request["fallbacks"] == "default" and claude.FALLBACK_BETA in request["betas"]
    assert request["output_config"]["effort"] == "high"
    assert request["output_config"]["format"] == {"type": "json_schema", "schema": claude.SCHEMA}
    prompt = request["messages"][0]["content"]
    for text in ("diff-a-text", "diff-b-text", "A body", "B title", '<file path="app.py">'):
        assert text in prompt


def test_unsafe_or_duplicate_file_names_are_rewritten(ctx):
    """Model output becomes file names; a name must never leave the scenario directory or overwrite another."""
    reply = message({"scenarios": [scenario("../evil.py"), scenario("helpers.py"),
                                   scenario("test_x.py"), scenario("dir/test_x.py")]})
    result = claude.ClaudeGenerator(client=FakeClient(reply)).generate(ctx)
    assert sorted(result.files) == ["test_evil.py", "test_helpers.py", "test_x.py", "test_x_2.py"]


@pytest.mark.parametrize("stop_reason", ["refusal", "max_tokens"])
def test_a_refused_or_truncated_reply_yields_no_scenarios_and_an_error(ctx, stop_reason):
    """A failed generation must count as a miss with a visible reason, not crash the run or pass silently."""
    reply = message(None, stop_reason=stop_reason)
    result = claude.ClaudeGenerator(client=FakeClient(reply)).generate(ctx)
    assert result.files == {}
    assert result.notes["error"] == stop_reason
    assert result.cost_usd > 0


def test_cost_uses_the_serving_models_price():
    usage = SimpleNamespace(input_tokens=1_000_000, output_tokens=1_000_000)
    assert claude.cost_usd("claude-opus-5-5", usage) == pytest.approx(24.0)
    assert math.isnan(claude.cost_usd("claude-unknown", usage))


def test_a_fallback_is_flagged_because_it_changes_whose_recall_this_is(ctx):
    iterations = [SimpleNamespace(type="message"), SimpleNamespace(type="fallback_message")]
    reply = message({"scenarios": [scenario("test_a.py")]}, model="claude-opus-4-8", iterations=iterations)
    result = claude.ClaudeGenerator(client=FakeClient(reply)).generate(ctx)
    assert result.notes["fallback"] and result.notes["cost_is_lower_bound"]
    assert result.models == ("claude-opus-4-8", "claude-opus-5-5")


def test_a_tree_too_large_for_the_prompt_fails_loudly(tmp_path):
    (tmp_path / "big.py").write_text("x" * (claude.MAX_TREE_CHARS + 1))
    with pytest.raises(claude.TreeTooLarge):
        claude.render_tree(tmp_path)


def test_the_tree_shows_python_and_the_root_readme_only(tmp_path):
    """A real repository's docs and lock files would crowd its code out of the prompt budget."""
    for name in ("README.md", "src/pkg/core.py", "docs/README.md", "uv.lock", "docs/guide.rst"):
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text(f"contents of {name}\n")
    shown = claude.render_tree(tmp_path)
    assert 'path="README.md"' in shown and 'path="src/pkg/core.py"' in shown
    assert "docs/" not in shown and "uv.lock" not in shown


def test_extra_import_roots_reach_the_prompt_only_when_set(ctx):
    """A src-layout package is not importable from the root; the model must know where to import from."""
    assert "also on sys.path" not in claude.render_prompt(ctx)
    src_layout = PairContext(ctx.base_tree, ctx.diff_a, ctx.diff_b, ctx.intent_a, ctx.intent_b, ("src",))
    assert "These directories are also on sys.path: src." in claude.render_prompt(src_layout)


def test_bench_runs_parsed_scenarios_and_never_sends_the_answer():
    """End to end at the API boundary: what leaves the machine has no oracle and no case id."""
    cases = [c for c in load_corpus(CORPUS) if not c.mined]  # decision 0002 keeps model scenarios off mined pairs
    client = FakeClient(message({"scenarios": [scenario("test_lost_response.py")]}))
    results = bench.run(cases, "claude", options={"client": client})

    by_id = {r.case.id: r for r in results}
    assert by_id["retry-x-nonce-key"].verdict == "conflict"
    assert by_id["retry-x-currency-key"].verdict == "clean"
    for case, request in zip(cases, client.requests):
        sent = request["system"] + request["messages"][0]["content"]
        assert case.id not in sent
        for oracle_source in generators.read_oracle(case).values():
            assert oracle_source not in sent
    assert all(r.record["generator"]["config"]["prompt"] == claude.PROMPT_DIGEST for r in results)
