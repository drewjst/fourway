from datetime import timedelta

import tomlkit


def test_parsed_date_inplace_add_keeps_comment_and_round_trips() -> None:
    doc = tomlkit.parse("  d = 1979-05-13  # keep\nx = 1  # n\n")
    doc["d"] += timedelta(days=1)
    doc["x"] += 1
    out = doc.as_string()
    assert out == "  d = 1979-05-14  # keep\nx = 2  # n\n"
    reparsed = tomlkit.parse(out)
    assert reparsed.as_string() == out


def test_factory_date_inplace_add_keeps_comment() -> None:
    doc = tomlkit.document()
    doc["d"] = tomlkit.date("1979-05-13")
    doc["d"].comment("keep")
    doc["d"] += timedelta(days=2)
    assert doc.as_string() == "d = 1979-05-15 # keep\n"
    assert tomlkit.parse(doc.as_string())["d"].as_string() == "1979-05-15"
