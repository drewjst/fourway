import pytest

import tomlkit
from tomlkit import parse


@pytest.mark.parametrize(
    "src",
    ["z = 3", "z = 3\n", "z = 3  # note\n"],
)
def test_key_value_item_appended_to_spaced_inline_table_uses_spaced_separator(
    src: str,
) -> None:
    doc = parse("a = {x = 1, y = 2}\n")
    _, v = tomlkit.key_value(src)
    doc["a"]["z"] = v

    rendered = doc.as_string()
    assert rendered == "a = {x = 1, y = 2, z = 3}\n"
    assert parse(rendered) == {"a": {"x": 1, "y": 2, "z": 3}}
    assert parse(rendered).as_string() == rendered


def test_trailing_space_from_key_value_is_not_doubled_by_next_separator() -> None:
    doc = parse("a = {x = 1, y = 2}\n")
    _, v = tomlkit.key_value("z = 3 ")
    doc["a"]["z"] = v
    doc["a"]["w"] = 4

    rendered = doc.as_string()
    assert rendered == "a = {x = 1, y = 2, z = 3, w = 4}\n"
    assert ",  " not in rendered
    assert parse(rendered) == {"a": {"x": 1, "y": 2, "z": 3, "w": 4}}
    assert parse(rendered).as_string() == rendered
