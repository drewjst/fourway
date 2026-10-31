import pytest

import tomlkit
from tomlkit import parse
from tomlkit.exceptions import UnexpectedCharError


@pytest.mark.parametrize(
    "src",
    ["z = 3, w = 4", "z = 3 , w = 4", "z = 3 junk", "z = 3}"],
)
def test_key_value_rejects_inline_table_style_trailing_input(src: str) -> None:
    with pytest.raises(UnexpectedCharError):
        tomlkit.key_value(src)


def test_key_value_comment_kept_on_item_but_dropped_in_inline_table() -> None:
    k, v = tomlkit.key_value("z = 3  # note\n")
    assert k.key == "z"
    assert v == 3
    assert v.trivia.comment == "# note"

    doc = parse("a = {x = 1, y = 2}\n")
    doc["a"]["z"] = v
    rendered = doc.as_string()

    assert "#" not in rendered
    assert parse(rendered) == {"a": {"x": 1, "y": 2, "z": 3}}
    assert parse(rendered).as_string() == rendered
