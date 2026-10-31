from datetime import timedelta

import tomlkit


def test_factory_date_arithmetic_result_does_not_alias_document_trivia() -> None:
    doc = tomlkit.document()
    doc["d"] = tomlkit.date("1979-05-13")
    doc["d"].comment("keep")
    before = doc.as_string()
    assert before == "d = 1979-05-13 # keep\n"

    original = doc["d"]
    result = original + timedelta(days=1)
    assert result.trivia is not original.trivia
    result.trivia.comment = "# MUTATED"
    result.trivia.indent = "    "

    assert doc.as_string() == before
    assert result.as_string() == "1979-05-14"


def test_factory_datetime_replace_result_does_not_alias_document_trivia() -> None:
    doc = tomlkit.document()
    doc["t"] = tomlkit.datetime("1979-05-13T12:34:56")
    doc["t"].comment("keep")
    before = doc.as_string()

    original = doc["t"]
    result = original.replace(year=2000)
    assert result.trivia is not original.trivia
    result.trivia.comment = "# MUTATED"

    assert doc.as_string() == before
    assert result.as_string() == "2000-05-13T12:34:56"
