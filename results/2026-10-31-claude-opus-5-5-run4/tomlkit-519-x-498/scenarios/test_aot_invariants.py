import pytest

from tomlkit import parse
from tomlkit.exceptions import ParseError


@pytest.mark.parametrize(
    "content",
    [
        "[[a]]\nx = 1\n\n[[a]]\nx = 2\n",
        "[[a]]  # comment\nx = 1\n",
        "[[fruit]]\napple.color = \"red\"\n\n[fruit.apple.texture]\nsmooth = true\n",
        "[[a.b]]\nx = 1\n\n[[a.b]]\nx = 2\n",
        "[[a]]",
    ],
)
def test_well_formed_aot_documents_round_trip(content: str) -> None:
    assert parse(content).as_string() == content


def test_plain_table_with_aot_name_after_unrelated_table_still_raises() -> None:
    content = "[[fruit]]\nx = 1\n\n[potato]\n\n[fruit]\ny = 2\n"
    with pytest.raises(ParseError):
        parse(content)


def test_duplicate_concrete_subtable_of_aot_element_still_raises() -> None:
    content = (
        "[[fruit]]\n"
        "[fruit.apple]\n"
        "x = 1\n"
        "\n"
        "[potato]\n"
        "\n"
        "[fruit.apple]\n"
        "y = 2\n"
    )
    with pytest.raises(ParseError):
        parse(content)
