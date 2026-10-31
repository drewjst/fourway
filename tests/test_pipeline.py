"""End-to-end runs on tiny synthetic repos, for the paths the corpus does not exercise."""

from pathlib import Path

import pytest

from fourway import gitops, pipeline


def make_pair(tmp_path: Path, base: dict, a: dict, b: dict) -> tuple[Path, str, str, str]:
    repo = gitops.init(tmp_path / "repo")

    def write(files: dict) -> None:
        for name, text in files.items():
            (repo / name).write_text(text)

    write(base)
    base_sha = gitops.commit_all(repo, "base")
    heads = []
    for name, files in (("a", a), ("b", b)):
        gitops.git(repo, "checkout", "--quiet", "-b", name, base_sha)
        write(files)
        heads.append(gitops.commit_all(repo, name))
    return repo, base_sha, heads[0], heads[1]


FLAGS = {"fa.py": "ON = False\n", "fb.py": "ON = False\n"}
A_ON = {"fa.py": "ON = True\n"}
B_ON = {"fb.py": "ON = True\n"}


def test_textual_conflicts_are_refused(tmp_path):
    """The product's premise is a clean merge; a textual conflict is git's job, not a finding."""
    repo, base, a, b = make_pair(tmp_path, {"x.py": "V = 1\n"}, {"x.py": "V = 2\n"}, {"x.py": "V = 3\n"})
    with pytest.raises(gitops.MergeConflict, match="x.py"):
        pipeline.verify(repo, base, a, b, {"test_x.py": "def test_x(): pass\n"}, tmp_path / "run")


def test_same_inputs_give_the_same_merge_sha(tmp_path):
    """Evidence is keyed on SHAs; if they drifted between runs, no record would ever match again."""
    first = make_pair(tmp_path / "1", FLAGS, A_ON, B_ON)
    second = make_pair(tmp_path / "2", FLAGS, A_ON, B_ON)
    assert first[1:] == second[1:]
    assert gitops.merge(first[0], *first[2:]) == gitops.merge(second[0], *second[2:])


def test_a_scenario_that_cannot_import_anywhere_is_unverified(tmp_path):
    """A broken scenario must read as no evidence, never as a conflict or as clean."""
    repo, base, a, b = make_pair(tmp_path, FLAGS, A_ON, B_ON)
    result = pipeline.verify(
        repo, base, a, b, {"test_broken.py": "import does_not_exist\n"}, tmp_path / "run"
    )
    assert set(result.findings.values()) == {"inconclusive"}
    assert result.verdict == "unverified"


def test_a_scenario_file_that_cannot_import_does_not_stop_the_others(tmp_path):
    """pytest stops the whole session on one collection error. In run 2, a scenario that imported
    B's new module did that on base, so a regression in A read as a lost B behavior: a false conflict."""
    repo, base, a, b = make_pair(tmp_path, FLAGS, A_ON, {**B_ON, "fb_new.py": "X = 1\n"})
    scenarios = {
        "test_a_breaks.py": "import fa\n\ndef test_flag_a_is_off():\n    assert not fa.ON\n",
        "test_b_module.py": "import fb_new\n\ndef test_b_module():\n    assert fb_new.X == 1\n",
    }
    result = pipeline.verify(repo, base, a, b, scenarios, tmp_path / "run")
    [regressed] = [t for t in result.outcomes if "test_a_breaks" in t]
    assert result.outcomes[regressed] == {"base": "passed", "a": "failed", "b": "passed", "ab": "failed"}
    assert result.findings[regressed] == "regression_a"
    assert result.verdict == "regression"


def test_a_hang_only_on_the_merge_is_an_emergent_conflict(tmp_path):
    repo, base, a, b = make_pair(tmp_path, FLAGS, A_ON, B_ON)
    scenario = (
        "import time\nimport fa, fb\n\n"
        "def test_finishes():\n"
        "    if fa.ON and fb.ON:\n"
        "        time.sleep(60)\n"
    )
    result = pipeline.verify(repo, base, a, b, {"test_hang.py": scenario}, tmp_path / "run", timeout=3)
    [(test, outcomes)] = result.outcomes.items()
    assert outcomes == {"base": "passed", "a": "passed", "b": "passed", "ab": "timeout"}
    assert result.findings[test] == "emergent"


def test_outcomes_that_change_between_repeats_are_flaky(tmp_path):
    """The false-positive target is under 5%; a flaky scenario counted as a conflict would blow it."""
    repo, base, a, b = make_pair(tmp_path, FLAGS, A_ON, B_ON)
    scenario = (
        "from pathlib import Path\n\n"
        "def test_fails_first_time_only():\n"
        "    marker = Path('ran-once')\n"
        "    first = not marker.exists()\n"
        "    marker.touch()\n"
        "    assert not first\n"
    )
    result = pipeline.verify(repo, base, a, b, {"test_flaky.py": scenario}, tmp_path / "run", repeat=2)
    assert set(result.findings.values()) == {"flaky"}
    assert result.verdict == "unverified"


def test_scenario_file_names_cannot_escape_the_scenario_directory(tmp_path):
    repo, base, a, b = make_pair(tmp_path, FLAGS, A_ON, B_ON)
    with pytest.raises(ValueError):
        pipeline.verify(repo, base, a, b, {"../test_escape.py": "def test_x(): pass\n"}, tmp_path / "run")
