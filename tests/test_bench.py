"""The benchmark itself must be able to come out wrong, or its numbers are not evidence."""

import dataclasses
import shutil
import tomllib
from collections import Counter
from pathlib import Path

import pytest

from fourway import bench, generators
from fourway.case import load_corpus
from fourway.sandbox import Sandbox

CORPUS = Path(__file__).parents[1] / "corpus"


def seeded() -> list:
    """The seeded cases. Mined pairs run their upstream suites in `fourway check-corpus`, which CI runs."""
    return [c for c in load_corpus(CORPUS) if not c.mined]


@pytest.fixture(scope="module")
def cases():
    return seeded()


@pytest.fixture(scope="module")
def scores(cases):
    return {name: bench.summarize(name, bench.run(cases, name)) for name in ("null", "oracle", "deranged")}


def test_corpus_has_conflicts_and_clean_controls(cases):
    labels = [c.label for c in cases]
    assert labels.count("conflict") >= 3 and labels.count("clean") >= 3


@pytest.mark.parametrize("case_id", [c.id for c in seeded()])
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
    """Writing nothing must not read as zero false positives: the rate's denominator is verified pairs only."""
    null = scores["null"]
    assert null.detected == 0 and null.false_positives == 0
    assert null.unverified == null.total
    assert null.cleans_verified == 0


def test_the_right_scenario_on_the_wrong_pair_detects_less(scores):
    """If a deranged oracle scored like the real one, recall would measure the corpus, not the generator."""
    assert scores["deranged"].detected < scores["oracle"].detected
    assert scores["deranged"].false_positives == 0


def test_a_deranged_case_never_gets_its_twins_oracle(cases):
    """Twins share change A and often the oracle; a twin as donor hands a case its own answer."""
    deranged = generators.Deranged(cases)
    for case in cases:
        donor = deranged._donor[case.id]
        assert donor.id != case.id and donor.conflict_class != case.conflict_class


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


def test_no_pull_request_appears_in_two_mined_pairs():
    """The false-positive interval treats pairs as independent; a shared change would count one trial twice."""
    mined = [c for c in load_corpus(CORPUS) if c.mined]
    urls = Counter(tomllib.loads((c.path / "case.toml").read_text())[s]["pr"] for c in mined for s in ("a", "b"))
    assert [url for url, n in urls.items() if n > 1] == []
    for case in mined:
        assert case.label == "clean" and case.expect is None
        assert case.a.commits[0] == case.base.commit


def test_model_scenarios_never_run_on_a_mined_pair(cases, monkeypatch, tmp_path):
    """Decision 0002: a mined pair's diffs are third-party input, so its scenarios run only in the sandbox."""
    called = []

    class Recorder:
        name = "recorder"

        def generate(self, ctx):
            called.append(ctx)
            return generators.Scenarios({})

    monkeypatch.setitem(generators.BLIND, "recorder", Recorder)
    mined = dataclasses.replace(
        cases[0], id="mined", a=dataclasses.replace(cases[0].a, commits=("0" * 40, "1" * 40))
    )
    with pytest.raises(ValueError, match="decision 0002"):
        bench.run([cases[0], mined], "recorder")
    with pytest.raises(ValueError, match="decision 0002"):
        bench.run([mined], "replay", options={"root": tmp_path})
    assert called == []
    bench.refuse_untrusted_locally([cases[0], mined], "recorder", Sandbox())  # the sandbox lifts the refusal


def test_false_positives_split_the_ways_the_corpus_fixed_in_advance(cases):
    """A headline rate over easy pairs flatters; each split counts exactly the verified pairs its tags name."""
    clean = next(c for c in cases if c.label == "clean")
    mined = dataclasses.replace(
        clean, id="mined", a=dataclasses.replace(clean.a, commits=("0" * 40, "1" * 40)),
        conflict_class="mined, same file", runtime=("a",), assisted=("a", "b"),
    )

    def result(case, verdict):
        return bench.CaseResult(case, generators.Scenarios({}), verdict, {}, 0.0, 0.0, {})

    unverified = dataclasses.replace(mined, id="unverified", conflict_class="mined, other files")
    results = [result(clean, "clean"), result(mined, "conflict"), result(unverified, "unverified")]
    assert bench.false_positive_breakdown(results) == [
        ("seeded twins", 0, 1),
        ("mined, same file", 1, 1),
        ("mined, other files", 0, 0),
        ("mined, both sides change code", 0, 0),
        ("mined, no side AI-credited", 0, 0),
    ]
    assert bench.false_positive_breakdown([result(clean, "conflict")]) == []
