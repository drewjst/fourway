"""The benchmark itself must be able to come out wrong, or its numbers are not evidence."""

import dataclasses
import shutil
from pathlib import Path

import pytest

from fourway import bench, generators
from fourway.case import load_corpus

CORPUS = Path(__file__).parents[1] / "corpus"


@pytest.fixture(scope="module")
def cases():
    return load_corpus(CORPUS)


@pytest.fixture(scope="module")
def scores(cases):
    return {name: bench.summarize(name, bench.run(cases, name)) for name in ("null", "oracle", "deranged")}


def test_corpus_has_conflicts_and_clean_controls(cases):
    labels = [c.label for c in cases]
    assert labels.count("conflict") >= 3 and labels.count("clean") >= 3


@pytest.mark.parametrize("case_id", [c.id for c in load_corpus(CORPUS)])
def test_every_case_matches_its_answer_key(cases, case_id):
    """A case whose oracle disagrees with its label would score every generator against a wrong answer."""
    [case] = [c for c in cases if c.id == case_id]
    assert bench.check_case(case) == []


def test_twins_make_the_same_change_a(cases):
    """A clean twin controls for change A only if A is identical; otherwise a generator can score by telling the A sides apart."""
    by_class: dict[str, list] = {}
    for case in cases:
        by_class.setdefault(case.conflict_class, []).append(case)
    twins = [group for group in by_class.values() if len(group) > 1]
    assert twins
    for group in twins:
        assert sorted(c.label for c in group) == ["clean", "conflict"]
        first, second = group

        def files(side):
            overlay = {p.relative_to(side.overlay): p.read_bytes() for p in side.overlay.rglob("*") if p.is_file()}
            return overlay, side.patch.read_bytes() if side.patch else None

        assert first.base == second.base
        assert first.a.intent == second.a.intent
        assert first.a.deleted == second.a.deleted
        assert files(first.a) == files(second.a)


def test_check_rejects_a_mislabeled_case(cases):
    case = next(c for c in cases if c.label == "conflict")
    problems = bench.check_case(dataclasses.replace(case, label="clean"))
    assert any("contradicts label" in p for p in problems)


def test_oracle_finds_every_conflict_and_flags_no_clean_pair(scores):
    oracle = scores["oracle"]
    assert oracle.detected == oracle.conflicts
    assert oracle.false_positives == 0


def test_no_scenarios_leaves_every_pair_unverified(scores):
    null = scores["null"]
    assert null.detected == 0 and null.false_positives == 0
    assert null.unverified == null.total


def test_the_right_scenario_on_the_wrong_pair_detects_less(scores):
    """If a deranged oracle scored like the real one, recall would measure the corpus, not the generator."""
    assert scores["deranged"].detected < scores["oracle"].detected
    assert scores["deranged"].false_positives == 0


def test_replay_reproduces_the_run_it_reads(cases, tmp_path):
    """A rescore after a runner fix credits the fix only if replaying unchanged files gives the original score."""
    original = bench.run(cases, "oracle")
    bench.save(original, bench.summarize("oracle", original), tmp_path)
    replayed = bench.run(cases, "replay", options={"root": tmp_path})
    assert [r.scenarios.files for r in replayed] == [r.scenarios.files for r in original]
    assert [r.verdict for r in replayed] == [r.verdict for r in original]

    shutil.rmtree(tmp_path / cases[0].id)
    [gone] = bench.run(cases[:1], "replay", options={"root": tmp_path})
    assert gone.verdict == "unverified" and "error" in gone.scenarios.notes


def test_blind_generators_never_see_the_answer(cases, monkeypatch):
    """Leaking an oracle or a label into the context would make any recall number meaningless."""
    seen = []

    class Recorder:
        name = "recorder"

        def generate(self, ctx):
            files = {p.relative_to(ctx.base_tree).as_posix(): p.read_bytes().decode(errors="replace")
                     for p in ctx.base_tree.rglob("*") if p.is_file()}
            seen.append((ctx, files))
            return generators.Scenarios({})

    monkeypatch.setitem(generators.BLIND, "recorder", Recorder)
    bench.run(cases, "recorder")
    for case, (ctx, files) in zip(cases, seen):
        visible = "\n".join([ctx.diff_a, ctx.diff_b, ctx.intent_a.body, ctx.intent_b.body, *files.values()])
        for oracle_source in generators.read_oracle(case).values():
            assert oracle_source not in visible
        assert case.id not in visible
        assert not any(name.startswith(("oracle", "case.toml")) for name in files)
